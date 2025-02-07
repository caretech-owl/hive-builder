import logging
import os
import subprocess
import signal
os.environ["GRADIO_ANALYTICS_ENABLED"] = "False"
import gradio as gr
import tempfile

from huggingface_hub import HfApi, whoami
from gradio_huggingfacehub_search import HuggingfaceHubSearch
from pathlib import Path


# https://huggingface.co/spaces/ggml-org/gguf-my-repo/blob/main/app.py
# https://huggingface.co/spaces/ggml-org/gguf-my-lora/blob/main/app.py

_LOGGER = logging.getLogger(__name__)

LLAMA_ROOT = Path("./llama.cpp")
CONVERSION_SCRIPT = LLAMA_ROOT / "convert_hf_to_gguf.py"
OUTPUTS_DIR = Path("/workspace/models")

# escape HTML for logging
def escape(s: str) -> str:
    s = s.replace("&", "&amp;") # Must be done first!
    s = s.replace("<", "&lt;")
    s = s.replace(">", "&gt;")
    s = s.replace('"', "&quot;")
    s = s.replace("\n", "<br/>")
    return s

def generate_importance_matrix(model_path: str, train_data_path: str, output_path: str):
    imatrix_command = [
        (LLAMA_ROOT / "llama-imatrix").as_posix(),
        "-m", model_path,
        "-f", train_data_path,
        "-ngl", "99",
        "--output-frequency", "10",
        "-o", output_path,
    ]

    if not os.path.isfile(model_path):
        raise Exception(f"Model file not found: {model_path}")

    _LOGGER.info("Running imatrix command...")
    process = subprocess.Popen(imatrix_command, shell=False)

    try:
        process.wait(timeout=60)  # added wait
    except subprocess.TimeoutExpired:
        _LOGGER.info("Imatrix computation timed out. Sending SIGINT to allow graceful termination...")
        process.send_signal(signal.SIGINT)
        try:
            process.wait(timeout=5)  # grace period
        except subprocess.TimeoutExpired:
            _LOGGER.warning("Imatrix proc still didn't term. Forecfully terming process...")
            process.kill()

    _LOGGER.info("Importance matrix generation completed.")

def split_upload_model(model_path: str, outdir: str, oauth_token: gr.OAuthToken | None, split_max_tensors=256, split_max_size=None):
    _LOGGER.debug(f"Model path: {model_path}")
    _LOGGER.debug(f"Output dir: {outdir}")

    if oauth_token is None or oauth_token.token is None:
        raise ValueError("You have to be logged in.")
    
    split_cmd = [
        (LLAMA_ROOT / "llama-gguf-split").as_posix(),
        "--split",
    ]
    if split_max_size:
        split_cmd.append("--split-max-size")
        split_cmd.append(split_max_size)
    else:
        split_cmd.append("--split-max-tensors")
        split_cmd.append(str(split_max_tensors))

    # args for output
    model_path_prefix = '.'.join(model_path.split('.')[:-1]) # remove the file extension
    split_cmd.append(model_path)
    split_cmd.append(model_path_prefix)

    _LOGGER.debug(f"Split command: {split_cmd}") 
    
    result = subprocess.run(split_cmd, shell=False, capture_output=True, text=True)
    _LOGGER.debug(f"Split command stdout: {result.stdout}") 
    _LOGGER.debug(f"Split command stderr: {result.stderr}") 
    
    if result.returncode != 0:
        stderr_str = result.stderr.decode("utf-8")
        raise Exception(f"Error splitting the model: {stderr_str}")
    _LOGGER.info("Model split successfully!")

    # remove the original model file if needed
    if os.path.exists(model_path):
        os.remove(model_path)

    model_file_prefix = model_path_prefix.split('/')[-1]
    _LOGGER.debug(f"Model file name prefix: {model_file_prefix}") 
    sharded_model_files = [f for f in os.listdir(outdir) if f.startswith(model_file_prefix) and f.endswith(".gguf")]
    if sharded_model_files:
        _LOGGER.info(f"Sharded model files: {sharded_model_files}")
        # api = HfApi(token=oauth_token.token)
        for file in sharded_model_files:
            file_path = os.path.join(outdir, file)
            # TODO: move file
            print(f"Uploading file: {file_path}")
            # try:
            #     api.upload_file(
            #         path_or_fileobj=file_path,
            #         path_in_repo=file,
            #         repo_id=repo_id,
            #     )
            # except Exception as e:
            #     raise Exception(f"Error uploading file {file_path}: {e}")
    else:
        raise Exception("No sharded files found.")
    
    _LOGGER.info("Sharded model has been created successfully!")

def process_model(model_id, q_method, use_imatrix, imatrix_q_method, private_repo, train_data_file, split_model, split_max_tensors, split_max_size, oauth_token: gr.OAuthToken | None):
    if oauth_token is None or oauth_token.token is None:
        raise gr.Error("You must be logged in to use GGUF-my-repo")

    # validate the oauth token
    try:
        whoami(oauth_token.token)
    except Exception as e:
        raise gr.Error("You must be logged in to use GGUF-my-repo")

    model_name = model_id.split('/')[-1]

    try:
        api = HfApi(token=oauth_token.token)

        dl_pattern = ["*.md", "*.json", "*.model"]

        pattern = (
            "*.safetensors"
            if any(
                file.path.endswith(".safetensors")
                for file in api.list_repo_tree(
                    repo_id=model_id,
                    recursive=True,
                )
            )
            else "*.bin"
        )

        dl_pattern += [pattern]

        if not os.path.exists("downloads"):
            os.makedirs("downloads")

        if not os.path.exists("outputs"):
            os.makedirs("outputs")

        with tempfile.TemporaryDirectory(dir="outputs") as outdir:
            fp16 = str(Path(outdir)/f"{model_name}.fp16.gguf")

            with tempfile.TemporaryDirectory(dir="downloads") as tmpdir:
                # Keep the model name as the dirname so the model name metadata is populated correctly
                local_dir = Path(tmpdir)/model_name
                _LOGGER.debug(local_dir)
                api.snapshot_download(repo_id=model_id, local_dir=local_dir, local_dir_use_symlinks=False, allow_patterns=dl_pattern)
                _LOGGER.info("Model downloaded successfully!")
                _LOGGER.info(f"Current working directory: {os.getcwd()}")
                _LOGGER.info(f"Model directory contents: {os.listdir(local_dir)}")

                config_dir = local_dir/"config.json"
                adapter_config_dir = local_dir/"adapter_config.json"
                if os.path.exists(adapter_config_dir) and not os.path.exists(config_dir):
                    raise Exception('adapter_config.json is present.<br/><br/>If you are converting a LoRA adapter to GGUF, please use <a href="https://huggingface.co/spaces/ggml-org/gguf-my-lora" target="_blank" style="text-decoration:underline">GGUF-my-lora</a>.')

                result = subprocess.run([
                    "python", CONVERSION_SCRIPT, local_dir, "--outtype", "f16", "--outfile", fp16
                ], shell=False, capture_output=True)
                _LOGGER.debug(result)
                if result.returncode != 0:
                    stderr_str = result.stderr.decode("utf-8")
                    raise Exception(f"Error converting to fp16: {stderr_str}")
                _LOGGER.info("Model converted to fp16 successfully!")
                _LOGGER.info(f"Converted model path: {fp16}")

            imatrix_path = Path(outdir)/"imatrix.dat"

            if use_imatrix:
                if train_data_file:
                    train_data_path = train_data_file.name
                else:
                    train_data_path = (LLAMA_ROOT / "groups_merged.txt").as_posix() #fallback calibration dataset

                _LOGGER.info(f"Training data file path: {train_data_path}")

                if not os.path.isfile(train_data_path):
                    raise Exception(f"Training data file not found: {train_data_path}")

                generate_importance_matrix(fp16, train_data_path, imatrix_path)
            else:
                _LOGGER.info("Not using imatrix quantization.")
            
            # Quantize the model
            quantized_gguf_name = f"{model_name.lower()}-{imatrix_q_method.lower()}-imat.gguf" if use_imatrix else f"{model_name.lower()}-{q_method.lower()}.gguf"
            quantized_gguf_path = str(Path(outdir)/quantized_gguf_name)
            if use_imatrix:
                quantise_ggml = [
                    (LLAMA_ROOT / "llama-quantize").as_posix(),
                    "--imatrix", imatrix_path, fp16, quantized_gguf_path, imatrix_q_method
                ]
            else:
                quantise_ggml = [
                    (LLAMA_ROOT / "llama-quantize").as_posix(),
                    fp16, quantized_gguf_path, q_method
                ]
            result = subprocess.run(quantise_ggml, shell=False, capture_output=True)
            if result.returncode != 0:
                stderr_str = result.stderr.decode("utf-8")
                raise Exception(f"Error quantizing: {stderr_str}")
            _LOGGER.info(f"Quantized successfully with {imatrix_q_method if use_imatrix else q_method} option!")
            _LOGGER.info(f"Quantized model path: {quantized_gguf_path}")

            # # Create empty repo
            # username = whoami(oauth_token.token)["name"]
            # new_repo_url = api.create_repo(repo_id=f"{username}/{model_name}-{imatrix_q_method if use_imatrix else q_method}-GGUF", exist_ok=True, private=private_repo)
            # new_repo_id = new_repo_url.repo_id
            # print("Repo created successfully!", new_repo_url)

            # try:
            #     card = ModelCard.load(model_id, token=oauth_token.token)
            # except:
            #     card = ModelCard("")
            # if card.data.tags is None:
            #     card.data.tags = []
            # card.data.tags.append("llama-cpp")
            # card.data.tags.append("gguf-my-repo")
            # card.data.base_model = model_id
            # card.text = dedent(
            #     f"""
            #     # {new_repo_id}
            #     This model was converted to GGUF format from [`{model_id}`](https://huggingface.co/{model_id}) using llama.cpp via the ggml.ai's [GGUF-my-repo](https://huggingface.co/spaces/ggml-org/gguf-my-repo) space.
            #     Refer to the [original model card](https://huggingface.co/{model_id}) for more details on the model.
                
            #     ## Use with llama.cpp
            #     Install llama.cpp through brew (works on Mac and Linux)
                
            #     ```bash
            #     brew install llama.cpp
                
            #     ```
            #     Invoke the llama.cpp server or the CLI.
                
            #     ### CLI:
            #     ```bash
            #     llama-cli --hf-repo {new_repo_id} --hf-file {quantized_gguf_name} -p "The meaning to life and the universe is"
            #     ```
                
            #     ### Server:
            #     ```bash
            #     llama-server --hf-repo {new_repo_id} --hf-file {quantized_gguf_name} -c 2048
            #     ```
                
            #     Note: You can also use this checkpoint directly through the [usage steps](https://github.com/ggerganov/llama.cpp?tab=readme-ov-file#usage) listed in the Llama.cpp repo as well.

            #     Step 1: Clone llama.cpp from GitHub.
            #     ```
            #     git clone https://github.com/ggerganov/llama.cpp
            #     ```

            #     Step 2: Move into the llama.cpp folder and build it with `LLAMA_CURL=1` flag along with other hardware-specific flags (for ex: LLAMA_CUDA=1 for Nvidia GPUs on Linux).
            #     ```
            #     cd llama.cpp && LLAMA_CURL=1 make
            #     ```

            #     Step 3: Run inference through the main binary.
            #     ```
            #     ./llama-cli --hf-repo {new_repo_id} --hf-file {quantized_gguf_name} -p "The meaning to life and the universe is"
            #     ```
            #     or 
            #     ```
            #     ./llama-server --hf-repo {new_repo_id} --hf-file {quantized_gguf_name} -c 2048
            #     ```
            #     """
            # )
            # readme_path = Path(outdir)/"README.md"
            # card.save(readme_path)

            if split_model:
                split_upload_model(str(quantized_gguf_path), outdir, oauth_token, split_max_tensors, split_max_size)
            else:
                try:
                    # TODO Move file
                    print(f"Uploading quantized model: {quantized_gguf_path}")
                    # api.upload_file(
                    #     path_or_fileobj=quantized_gguf_path,
                    #     path_in_repo=quantized_gguf_name,
                    #     repo_id=new_repo_id,
                    # )
                except Exception as e:
                    raise Exception(f"Error uploading quantized model: {e}")
            
            if os.path.isfile(imatrix_path):
                try:
                    # TODO Move file
                    print(f"Uploading imatrix.dat: {imatrix_path}")
                    # api.upload_file(
                    #     path_or_fileobj=imatrix_path,
                    #     path_in_repo="imatrix.dat",
                    #     repo_id=new_repo_id,
                    # )
                except Exception as e:
                    raise Exception(f"Error uploading imatrix.dat: {e}")

            # TODO Move file
            # api.upload_file(
            #     path_or_fileobj=readme_path,
            #     path_in_repo="README.md",
            #     repo_id=new_repo_id,
            # )
            print(f"Uploaded successfully with {imatrix_q_method if use_imatrix else q_method} option!")

        # end of the TemporaryDirectory(dir="outputs") block; temporary outputs are deleted here

        return (
            f'<h1>✅ DONE</h1><br/>Find your repo here: <a href="{new_repo_url}" target="_blank" style="text-decoration:underline">{new_repo_id}</a>',
            "llama.png",
        )
    except Exception as e:
        return (f'<h1>❌ ERROR</h1><br/><pre style="white-space:pre-wrap;">{escape(str(e))}</pre>', "error.png")


css="""/* Custom CSS to allow scrolling */
.gradio-container {overflow-y: auto;}
"""
# Create Gradio interface
with gr.Blocks(css=css) as demo: 
    gr.Markdown("You must be logged in to use GGUF-my-repo.")
    gr.LoginButton(min_width=250)

    model_id = HuggingfaceHubSearch(
        label="Hub Model ID",
        placeholder="Search for model id on Huggingface",
        search_type="model",
    )

    q_method = gr.Dropdown(
        ["Q2_K", "Q3_K_S", "Q3_K_M", "Q3_K_L", "Q4_0", "Q4_K_S", "Q4_K_M", "Q5_0", "Q5_K_S", "Q5_K_M", "Q6_K", "Q8_0"],
        label="Quantization Method",
        info="GGML quantization type",
        value="Q4_K_M",
        filterable=False,
        visible=True
    )

    imatrix_q_method = gr.Dropdown(
        ["IQ3_M", "IQ3_XXS", "Q4_K_M", "Q4_K_S", "IQ4_NL", "IQ4_XS", "Q5_K_M", "Q5_K_S"],
        label="Imatrix Quantization Method",
        info="GGML imatrix quants type",
        value="IQ4_NL", 
        filterable=False,
        visible=False
    )

    use_imatrix = gr.Checkbox(
        value=False,
        label="Use Imatrix Quantization",
        info="Use importance matrix for quantization."
    )

    private_repo = gr.Checkbox(
        value=False,
        label="Private Repo",
        info="Create a private repo under your username."
    )

    train_data_file = gr.File(
        label="Training Data File",
        file_types=["txt"],
        visible=False
    )

    split_model = gr.Checkbox(
        value=False,
        label="Split Model",
        info="Shard the model using gguf-split."
    )

    split_max_tensors = gr.Number(
        value=256,
        label="Max Tensors per File",
        info="Maximum number of tensors per file when splitting model.",
        visible=False
    )

    split_max_size = gr.Textbox(
        label="Max File Size",
        info="Maximum file size when splitting model (--split-max-size). May leave empty to use the default. Accepted suffixes: M, G. Example: 256M, 5G",
        visible=False
    )

    def update_visibility(use_imatrix):
        return gr.update(visible=not use_imatrix), gr.update(visible=use_imatrix), gr.update(visible=use_imatrix)
    
    use_imatrix.change(
        fn=update_visibility,
        inputs=use_imatrix,
        outputs=[q_method, imatrix_q_method, train_data_file]
    )

    iface = gr.Interface(
        fn=process_model,
        inputs=[
            model_id,
            q_method,
            use_imatrix,
            imatrix_q_method,
            private_repo,
            train_data_file,
            split_model,
            split_max_tensors,
            split_max_size,
        ],
        outputs=[
            gr.Markdown(label="output"),
            gr.Image(show_label=False),
        ],
        title="Create your own GGUF Quants, blazingly fast ⚡!",
        description="The space takes an HF repo as an input, quantizes it and creates a Public repo containing the selected quant under your HF user namespace.",
        api_name=False
    )

    def update_split_visibility(split_model):
        return gr.update(visible=split_model), gr.update(visible=split_model)

    split_model.change(
        fn=update_split_visibility,
        inputs=split_model,
        outputs=[split_max_tensors, split_max_size]
    )


# Launch the interface
demo.queue(default_concurrency_limit=1, max_size=5).launch(debug=True, show_api=False)