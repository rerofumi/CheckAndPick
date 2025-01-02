LCM_WORKFLOW = """
{
  "4": {
    "inputs": {
      "ckpt_name": "catTowerNoobaiXL_v10.safetensors"
    },
    "class_type": "CheckpointLoaderSimple",
    "_meta": {
      "title": "Load Checkpoint"
    }
  },
  "6": {
    "inputs": {
      "text": "masterpiece, best quality, newest, absurdres, highres, 1girl, loli, gothic_lolita, sofa",
      "speak_and_recognation": true,
      "clip": [
        "32",
        1
      ]
    },
    "class_type": "CLIPTextEncode",
    "_meta": {
      "title": "CLIP Text Encode (Prompt)"
    }
  },
  "7": {
    "inputs": {
      "text": "worst quality, old, early, low quality, lowres, signature, username, logo, bad hands, mutated hands, mammal, anthro, furry, ambiguous form, feral, semi-anthro, 3d, 3dcg",
      "speak_and_recognation": true,
      "clip": [
        "32",
        1
      ]
    },
    "class_type": "CLIPTextEncode",
    "_meta": {
      "title": "CLIP Text Encode (Prompt)"
    }
  },
  "8": {
    "inputs": {
      "samples": [
        "10",
        0
      ],
      "vae": [
        "4",
        2
      ]
    },
    "class_type": "VAEDecode",
    "_meta": {
      "title": "VAE Decode"
    }
  },
  "10": {
    "inputs": {
      "add_noise": true,
      "noise_seed": 127604760303591,
      "cfg": 2,
      "model": [
        "16",
        0
      ],
      "positive": [
        "6",
        0
      ],
      "negative": [
        "7",
        0
      ],
      "sampler": [
        "11",
        0
      ],
      "sigmas": [
        "12",
        0
      ],
      "latent_image": [
        "15",
        0
      ]
    },
    "class_type": "SamplerCustom",
    "_meta": {
      "title": "SamplerCustom"
    }
  },
  "11": {
    "inputs": {
      "sampler_name": "lcm"
    },
    "class_type": "KSamplerSelect",
    "_meta": {
      "title": "KSamplerSelect"
    }
  },
  "12": {
    "inputs": {
      "scheduler": "sgm_uniform",
      "steps": 4,
      "denoise": 1,
      "model": [
        "16",
        0
      ]
    },
    "class_type": "BasicScheduler",
    "_meta": {
      "title": "BasicScheduler"
    }
  },
  "15": {
    "inputs": {
      "width": 1024,
      "height": 1024,
      "batch_size": 1
    },
    "class_type": "EmptyLatentImage",
    "_meta": {
      "title": "Empty Latent Image"
    }
  },
  "16": {
    "inputs": {
      "sampling": "lcm",
      "zsnr": false,
      "model": [
        "32",
        0
      ]
    },
    "class_type": "ModelSamplingDiscrete",
    "_meta": {
      "title": "ModelSamplingDiscrete"
    }
  },
  "19": {
    "inputs": {
      "lora_name": "lora-ix-tillhi-v1.safetensors",
      "strength_model": 1,
      "strength_clip": 1,
      "model": [
        "4",
        0
      ],
      "clip": [
        "4",
        1
      ]
    },
    "class_type": "LoraLoader",
    "_meta": {
      "title": "Load LoRA"
    }
  },
  "26": {
    "inputs": {
      "filename_prefix": "2025-01-02/Rough",
      "images": [
        "8",
        0
      ]
    },
    "class_type": "SaveImage",
    "_meta": {
      "title": "Save Image"
    }
  },
  "32": {
    "inputs": {
      "lora_name": "lcm_lora_sdxl.safetensors",
      "strength_model": 1,
      "strength_clip": 1,
      "model": [
        "19",
        0
      ],
      "clip": [
        "19",
        1
      ]
    },
    "class_type": "LoraLoader",
    "_meta": {
      "title": "Load LoRA"
    }
  }
}
"""
