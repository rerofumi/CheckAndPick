import datetime
import json
import random
import time

import click
import fm_comfyui_bridge.bridge
import gradio as gr
from fm_comfyui_bridge.lora_yaml import SdLoraYaml
from PIL import Image

import CheckAndPick.comfy_api as comfy_api
import CheckAndPick.config as config

NEGATIVE_PROMPT = "lowres, (bad), text, error, fewer, extra, missing, worst quality, jpeg artifacts, low quality, watermark, unfinished, displeasing, oldest, early, chromatic aberration, signature, extra digits, artistic error, username, scan, abstract, (((cg, 3dcg)))  dialogue, dialogue ballon"

# 灰色の画像を9つ作成し、リストに格納
draft_images = [Image.new("RGB", (1024, 1024), color="gray") for _ in range(9)]

# 選択したイメージのリスト
pickup_images = []

# 選択中のイメージ
select_draft_index = 0
select_pickup_index = 0

# lora yaml
lora = SdLoraYaml()


def generate_draft(positive, negative, progress_bar=gr.Progress()):
    global draft_images
    images = []
    prompt_path = json.loads(comfy_api.LCM_WORKFLOW)
    # パラメータ埋め込み
    prompt_path[config.COMFYUI_NODE_CHECKPOINT]["inputs"]["ckpt_name"] = lora.data[
        "lcm"
    ]["checkpoint"]
    prompt_path[config.COMFYUI_NODE_PROMPT]["inputs"]["text"] = (
        f"{lora.trigger}, {positive}"
    )
    prompt_path[config.COMFYUI_NODE_NEGATIVE]["inputs"]["text"] = negative
    prompt_path[config.COMFYUI_NODE_SEED]["inputs"]["noise_seed"] = random.randint(
        1, 10000000000
    )
    prompt_path[config.COMFYUI_NODE_SIZE]["inputs"]["width"] = lora.image_size[0]
    prompt_path[config.COMFYUI_NODE_SIZE]["inputs"]["height"] = lora.image_size[1]
    prompt_path[config.COMFYUI_NODE_LORA_CHECKPOINT]["inputs"]["lora_name"] = lora.model
    prompt_path[config.COMFYUI_NODE_LORA_CHECKPOINT]["inputs"]["strength_model"] = (
        lora.strength
    )
    prompt_path[config.COMFYUI_NODE_LORA_CHECKPOINT]["inputs"]["strength_clip"] = (
        lora.strength
    )
    current_date = datetime.datetime.now().strftime("%Y-%m-%d")
    prompt_path[config.COMFYUI_NODE_OUTPUT]["inputs"]["filename_prefix"] = (
        f"{current_date}/Bridge"
    )
    if not lora.lora_enabled:
        prompt_path[config.COMFYUI_NODE_LORA_CHECKPOINT]["inputs"]["strength_model"] = 0
        prompt_path[config.COMFYUI_NODE_LORA_CHECKPOINT]["inputs"]["strength_clip"] = 0
    prompt_path[config.COMFYUI_NODE_LCM_LORA]["inputs"]["lora_name"] = lora.data["lcm"][
        "lora"
    ]
    # draft 生成
    for _ in progress_bar.tqdm(range(9), desc="Generating drafts...", total=9):
        prompt_path[config.COMFYUI_NODE_SEED]["inputs"]["noise_seed"] = random.randint(
            1, 10000000000
        )
        id = fm_comfyui_bridge.bridge.send_request(prompt_path)
        if id:
            fm_comfyui_bridge.bridge.await_request(1, 3)
            image = fm_comfyui_bridge.bridge.get_image(
                id, output_node=config.COMFYUI_NODE_OUTPUT
            )
            images.append(image)
        else:
            break

    draft_images = images

    return draft_images


def draft_select(evt: gr.SelectData):
    global select_draft_index
    select_draft_index = evt.index


def pickup_select(evt: gr.SelectData):
    global select_pickup_index
    select_pickup_index = evt.index


def pickup():
    global select_draftindex, draft_images
    pickup_images.append(draft_images[select_draft_index])
    return pickup_images


def remove_pickup():
    del pickup_images[select_pickup_index]
    return pickup_images


def add_pickup(image):
    if image is None:
        return None
    # PIL Imageオブジェクトとして処理
    img = Image.fromarray(image)
    pickup_images.append(img)
    return [None, pickup_images]


def save_pickup(positive, negative, progress_bar=gr.Progress()):
    current_time = int(time.time())
    for image in progress_bar.tqdm(
        pickup_images, desc="Generating drafts...", total=len(pickup_images)
    ):
        fm_comfyui_bridge.bridge.save_image(
            image,
            f"{lora.trigger}, {positive}",
            negative,
            filename=f"pickup_{current_time}.png",
            workspace="./",
            output_dir="outputs",
        )
        current_time += 1


def clear_pickup():
    global pickup_images
    pickup_images = []
    return pickup_images


def rendering(positive, negative, progress_bar=gr.Progress()):
    global pickup_images, lora
    result = []
    pickups = pickup_images.copy()
    if pickups is None:
        return None
    if pickups == []:
        return None
    for draft in progress_bar.tqdm(pickups, desc="Generating...", total=len(pickups)):
        current_time = int(time.time())
        fm_comfyui_bridge.bridge.save_image(
            draft,
            f"{lora.trigger}, {positive}",
            negative,
            filename=f"draft_{current_time}.png",
            workspace="./",
            output_dir="outputs",
        )
        image = fm_comfyui_bridge.bridge.generate_i2i_highreso(
            f"{lora.trigger}, {positive}",
            negative,
            lora,
            lora.image_size,
            f"./outputs/draft_{current_time}.png",
        )
        fm_comfyui_bridge.bridge.save_image(
            image,
            f"{lora.trigger}, {positive}",
            negative,
            filename=f"fine_{current_time}.png",
            workspace="./",
            output_dir="outputs",
        )
        result.append(image)
    return result


def gui():
    with gr.Blocks(theme=gr.themes.Ocean()) as demo:
        # Positive Prompt
        positive_prompt = gr.Textbox(
            label="Positive Prompt",
            placeholder="Enter positive prompt here",
            value="masterpiece, best quality, 1girl",
        )

        # Negative Prompt
        negative_prompt = gr.Textbox(
            value=NEGATIVE_PROMPT,
            label="Negative Prompt",
            placeholder="Enter negative prompt here",
        )

        # Draft generate button
        draft_button = gr.Button("Draft generate button")

        # Draft images gallery
        gallery = gr.Gallery(
            value=draft_images,
            rows=3,
            columns=3,
            label="Select a draft image",
        )

        # Pickup draft button
        pickup_button = gr.Button("Pickup")

        # Draft images gallery
        pickup_gallery = gr.Gallery(
            value=pickup_images,
            columns=3,
            label="Pickups",
        )

        # pickup editor
        with gr.Accordion("Edit pickup", open=False):
            with gr.Row():
                save_pickup_button = gr.Button("Save pickup image(s)")
                remove_pickup_button = gr.Button("Remove")
                clear_pickup_button = gr.Button("Clear", variant="stop")
            add_pickup_image = gr.Image(label="Add Pickup Image")

        # Final rendering button
        rendering_button = gr.Button("Refine")

        # Generate Image display
        generate_image = gr.Gallery(
            value=None, label="Generate Image", interactive=False
        )

        #
        # Events
        #
        draft_button.click(
            fn=generate_draft,
            inputs=[positive_prompt, negative_prompt],
            outputs=gallery,
        )
        gallery.select(fn=draft_select, inputs=None, outputs=None)
        #
        pickup_button.click(fn=pickup, outputs=pickup_gallery)
        save_pickup_button.click(
            fn=save_pickup, inputs=[positive_prompt, negative_prompt], outputs=None
        )
        remove_pickup_button.click(fn=remove_pickup, outputs=pickup_gallery)
        clear_pickup_button.click(fn=clear_pickup, outputs=pickup_gallery)
        pickup_gallery.select(fn=pickup_select, inputs=None, outputs=None)
        add_pickup_image.upload(
            fn=add_pickup,
            inputs=add_pickup_image,
            outputs=[add_pickup_image, pickup_gallery],
        )

        # Rendering events
        rendering_button.click(
            fn=rendering,
            inputs=[positive_prompt, negative_prompt],
            outputs=generate_image,
        )

    #
    demo.queue()
    demo.launch()


# CLI main function
@click.command("CheckAndPick", help="ComfyUI frontend")
@click.argument("lora_yaml", type=str)
def run(lora_yaml: str):
    global lora
    lora.read_from_yaml(lora_yaml)
    gui()
