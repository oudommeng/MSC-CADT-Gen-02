import torch

checkpoint_path = "yolo_model_checkpoint.pth"
checkpoint = torch.load(checkpoint_path, map_location="cpu")
print("Total keys:", len(checkpoint))
non_backbone_keys = [k for k in checkpoint.keys() if not k.startswith("feature_mapper.layer") and not k.startswith("feature_mapper.bn")]
print("Non-backbone keys:", non_backbone_keys)
