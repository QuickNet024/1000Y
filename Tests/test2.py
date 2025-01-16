import torch
import torchvision
import torchaudio

# 检查 CUDA 是否可用
print(torch.cuda.is_available())  # 应该返回 True

# 检查 PyTorch 版本
print(torch.__version__)  # 应该返回 '2.4.1+cu118'

# 检查 torchvision 版本
print(torchvision.__version__)  # 应该返回 '0.19.1+cu118'

# 检查 torchaudio 版本
print(torchaudio.__version__)  # 应该返回 '2.4.1+cu118'

# 检查 CUDA 版本
print(torch.version.cuda)  # 应该返回 '11.8'

# 检查 GPU 设备
print(torch.cuda.get_device_name(0))  # 应该返回你的 GPU 型号