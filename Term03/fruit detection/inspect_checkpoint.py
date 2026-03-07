import torch

checkpoint_path = "yolo_model_checkpoint.pth"
checkpoint = torch.load(checkpoint_path, map_location="cpu")
print("Type of checkpoint:", type(checkpoint))
if isinstance(checkpoint, dict):
    print("Keys in checkpoint:", list(checkpoint.keys()))
    if 'model_state_dict' in checkpoint:
        print("model_state_dict keys sample:", list(checkpoint['model_state_dict'].keys())[:5])
    else:
        print("Checkpoint is a state_dict direct. State_dict keys sample:", list(checkpoint.keys())[:5])
else:
    print("Checkpoint is a model instance of class:", type(checkpoint))
