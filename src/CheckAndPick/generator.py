import datetime
import importlib.resources
import json
import random
import time

import fm_comfyui_bridge.bridge
import fm_comfyui_bridge.lora_yaml

import CheckAndPick.config as config


#
# ドラフト生成
#
def draft_prompt(
    positive: str, negative: str, lora: fm_comfyui_bridge.lora_yaml.SdLoraYaml
):
    with importlib.resources.open_text(
        "CheckAndPick.Workflow", "SDXL_LoRA_LCM_Lightning_API.json"
    ) as f:
        workflow_node = json.load(f)
    # パラメータ埋め込み
    workflow_node[config.COMFYUI_NODE_CHECKPOINT]["inputs"]["ckpt_name"] = lora.data[
        "lcm"
    ]["checkpoint"]
    workflow_node[config.COMFYUI_NODE_PROMPT]["inputs"]["text"] = (
        f"{lora.trigger}, {positive}"
    )
    workflow_node[config.COMFYUI_NODE_NEGATIVE]["inputs"]["text"] = negative
    workflow_node[config.COMFYUI_NODE_SEED]["inputs"]["noise_seed"] = random.randint(
        1, 10000000000
    )
    workflow_node[config.COMFYUI_NODE_SIZE]["inputs"]["width"] = lora.image_size[0]
    workflow_node[config.COMFYUI_NODE_SIZE]["inputs"]["height"] = lora.image_size[1]
    current_date = datetime.datetime.now().strftime("%Y-%m-%d")
    workflow_node[config.COMFYUI_NODE_OUTPUT]["inputs"]["filename_prefix"] = (
        f"{current_date}/Bridge"
    )
    if not lora.lora_enabled:
        workflow_node[config.COMFYUI_NODE_LORA_CHECKPOINT]["inputs"][
            "strength_model"
        ] = 0
        workflow_node[config.COMFYUI_NODE_LORA_CHECKPOINT]["inputs"][
            "strength_clip"
        ] = 0
    workflow_node[config.COMFYUI_NODE_LCM_LORA]["inputs"]["lora_name"] = lora.data[
        "lcm"
    ]["lora"]
    # lora
    workflow_node = fm_comfyui_bridge.bridge.insert_loras(
        workflow_node, lora, config.COMFYUI_NODE_CHECKPOINT
    )
    return workflow_node


def drafts(workflow_node, server_url=None):
    workflow_node[config.COMFYUI_NODE_SEED]["inputs"]["noise_seed"] = random.randint(
        1, 10000000000
    )
    id = fm_comfyui_bridge.bridge.send_request(workflow_node, server_url)
    if id:
        fm_comfyui_bridge.bridge.await_request(1, 3, server_url)
        image = fm_comfyui_bridge.bridge.get_image(
            id, output_node=config.COMFYUI_NODE_OUTPUT, server_url=server_url
        )
        return image

    return None


#
# Highreso Generator
#
def t2i_highreso_request_build(
    prompt: str,
    negative: str,
    lora: fm_comfyui_bridge.lora_yaml.SdLoraYaml,
) -> any:
    with importlib.resources.open_text(
        "CheckAndPick.Workflow", "SDXL_HighReso_I2I_API.json"
    ) as f:
        workflow_node = json.load(f)
    # パラメータ埋め込み(workflowによって異なる処理)
    workflow_node[config.COMFYUI_NODE_HR_CHECKPOINT]["inputs"]["ckpt_name"] = (
        lora.checkpoint
    )
    workflow_node[config.COMFYUI_NODE_HR_PROMPT]["inputs"]["text"] = prompt
    workflow_node[config.COMFYUI_NODE_HR_NEGATIVE]["inputs"]["text"] = negative
    for node in config.COMFYUI_NODE_HR_SEED:
        workflow_node[node]["inputs"]["noise_seed"] = random.randint(1, 10000000000)
    current_date = datetime.datetime.now().strftime("%Y-%m-%d")
    workflow_node[config.COMFYUI_NODE_HR_OUTPUT]["inputs"]["filename_prefix"] = (
        f"{current_date}/Bridge"
    )
    # prediction
    if lora.vpred:
        for node in config.COMFYUI_NODE_HR_SAMPLING_DISCRETE:
            workflow_node[node]["inputs"]["sampling"] = "v_prediction"
    else:
        for node in config.COMFYUI_NODE_HR_SAMPLING_DISCRETE:
            workflow_node[node]["inputs"]["sampling"] = "eps"
    # lora
    workflow_node = fm_comfyui_bridge.bridge.insert_loras(
        workflow_node, lora, config.COMFYUI_NODE_HR_CHECKPOINT
    )
    return workflow_node


def highreso(draft, positive, negative, lora, server_url=None):
    current_time = int(time.time())
    upload_image = f"draft_{current_time}.png"
    fm_comfyui_bridge.bridge.save_image(
        draft,
        f"{lora.trigger}, {positive}",
        negative,
        filename=upload_image,
        workspace="./",
        output_dir="outputs",
    )
    #
    fm_comfyui_bridge.bridge.send_image(
        f"./outputs/{upload_image}", upload_name=upload_image, server_url=server_url
    )
    prompt = t2i_highreso_request_build(positive, negative, lora)
    prompt[config.COMFYUI_NODE_HR_LOAD_IMAGE]["inputs"]["image"] = upload_image
    #
    id = fm_comfyui_bridge.bridge.send_request(prompt, server_url)
    if id:
        fm_comfyui_bridge.bridge.await_request(1, 3, server_url)
        image = fm_comfyui_bridge.bridge.get_image(
            id, output_node=config.COMFYUI_NODE_HR_OUTPUT, server_url=server_url
        )
    else:
        raise Exception("Request failed")
    #
    fm_comfyui_bridge.bridge.save_image(
        image,
        f"{lora.trigger}, {positive}",
        negative,
        filename=f"fine_{current_time}.png",
        workspace="./",
        output_dir="outputs",
    )
    return image
