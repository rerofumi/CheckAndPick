import time

import click
import fm_comfyui_bridge.bridge
import gradio as gr
from fm_comfyui_bridge.lora_yaml import SdLoraYaml
from PIL import Image

import CheckAndPick.generator as generator

POSITIVE_PROMPT = "masterpiece, best quality, 1girl"
NEGATIVE_PROMPT = "worst quality, bad quality, low quality, lowres, scan artifacts, jpeg artifacts, sketch, light particles"


# 灰色の画像を9つ作成し、リストに格納
draft_images = [Image.new("RGB", (1024, 1024), color="gray") for _ in range(9)]

# 選択したイメージのリスト
pickup_images = []

# 選択中のイメージ
select_draft_index = 0
select_pickup_index = 0

# lora yaml
lora = SdLoraYaml()

# ComfyUI host URL
comfyui_host = None


#
# ComfyUI API
#
def generate_draft(positive, negative, progress_bar=gr.Progress()):
    global draft_images, lora
    images = []
    prompt_path = generator.draft_prompt(positive, negative, lora)
    # draft 生成
    for _ in progress_bar.tqdm(range(9), desc="Generating drafts...", total=9):
        images.append(generator.drafts(prompt_path, server_url=comfyui_host))
    draft_images = images

    return images


def rendering(positive, negative, progress_bar=gr.Progress()):
    global pickup_images, lora
    result = []
    pickups = pickup_images.copy()
    if pickups is None:
        return None
    if pickups == []:
        return None
    for draft in progress_bar.tqdm(pickups, desc="Generating...", total=len(pickups)):
        result.append(
            generator.highreso(draft, positive, negative, lora, server_url=comfyui_host)
        )
    return result


#
# UI handlers
#


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


#
# UI main
#


def gui(positivive, negative, listen):
    with gr.Blocks(theme=gr.themes.Ocean()) as demo:
        # Positive Prompt
        positive_prompt = gr.Textbox(
            label="Positive Prompt",
            placeholder="Enter positive prompt here",
            value=positivive,
        )

        # Negative Prompt
        negative_prompt = gr.Textbox(
            value=negative,
            label="Negative Prompt",
            placeholder="Enter negative prompt here",
        )

        # Draft generate button
        draft_button = gr.Button("Draft generate")

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
        with gr.Accordion("Edit pickups", open=False):
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
    demo.launch(share=False, inbrowser=True, server_name=listen)


#
# CLI main function
#
@click.command("CheckAndPick", help="ComfyUI frontend")
@click.argument("lora_yaml", type=str)
@click.option("-h", "--host", default=None, help="Specify the ComfyUI host address")
@click.option("-l", "--listen", default=None, help="Specify the server listen address")
def run(lora_yaml: str, host=None, listen=None):
    global lora, comfyui_host
    comfyui_host = host
    if listen is None:
        listen = "127.0.0.1"
    lora.read_from_yaml(lora_yaml)
    positive = POSITIVE_PROMPT
    negative = NEGATIVE_PROMPT
    if "prompt" in lora.data:
        if "positive" in lora.data["prompt"]:
            positive = lora.data["prompt"]["positive"]
        if "negative" in lora.data["prompt"]:
            negative = lora.data["prompt"]["negative"]
    gui(positive, negative, listen)
