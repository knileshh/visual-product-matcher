# Enable GPU Processing for Visual Product Matcher

## Current Status
- PyTorch Version: 2.1.0+cpu (CPU-only)
- CUDA: Not available
- GPU Hardware: RTX 3050 4GB

## Steps to Enable GPU Processing

### 1. Check NVIDIA Driver and CUDA Compatibility

First, check your NVIDIA driver version:
```powershell
nvidia-smi
```

This will show your GPU and driver version. Your RTX 3050 supports CUDA 11.x and 12.x.

### 2. Uninstall CPU-Only PyTorch

```powershell
pip uninstall torch torchvision torchaudio
```

**Important**: Say "yes" to uninstall all three packages.

### 3. Install CUDA-Enabled PyTorch

Choose based on your CUDA preference:

#### Option A: CUDA 11.8 (Recommended - More Stable)
```powershell
pip install torch==2.1.0 torchvision==0.16.0 --index-url https://download.pytorch.org/whl/cu118
```

#### Option B: CUDA 12.1 (Latest)
```powershell
pip install torch==2.1.0 torchvision==0.16.0 --index-url https://download.pytorch.org/whl/cu121
```

### 4. Verify GPU is Detected

```powershell
python -c "import torch; print('CUDA available:', torch.cuda.is_available()); print('GPU:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'N/A'); print('CUDA version:', torch.version.cuda)"
```

Expected output:
```
CUDA available: True
GPU: NVIDIA GeForce RTX 3050 Laptop GPU
CUDA version: 11.8 (or 12.1)
```

### 5. Clean Data and Rebuild with GPU

Since the database has duplicate entries, start fresh:

```powershell
# Remove old data
Remove-Item data/products.db -ErrorAction SilentlyContinue
Remove-Item data/embeddings/* -Recurse -ErrorAction SilentlyContinue
Remove-Item data/index/* -Recurse -ErrorAction SilentlyContinue

# Rebuild with GPU acceleration
python init_data.py
```

## Expected Performance Improvements

| Metric | CPU (Current) | GPU (RTX 3050) | Speedup |
|--------|---------------|----------------|---------|
| Images/sec | ~89 | ~300-400 | 3-5x |
| Total Time (42,700 images) | ~8 minutes | ~2-3 minutes | 3-4x |
| Batch Size | 32 | 64-128 | 2-4x larger |

## Configuration Optimization (Optional)

After GPU is working, you can increase batch size in `config.yaml`:

```yaml
ml:
  clip_model: "ViT-B/32"
  device: "cuda"  # Already set correctly
  embedding_dimension: 512
  batch_size: 64  # Increase from 32 to 64 or 128 for GPU
```

## Troubleshooting

### Issue: CUDA out of memory
**Solution**: Reduce batch_size in config.yaml (try 32, then 48, then 64)

### Issue: Still showing CPU
**Solution**: 
1. Make sure you uninstalled the old torch completely
2. Check pip list: `pip list | Select-String torch`
3. Should show torch-2.1.0+cu118 (not +cpu)

### Issue: nvidia-smi command not found
**Solution**: Update your NVIDIA GPU drivers from https://www.nvidia.com/Download/index.aspx

## Notes

- The RTX 3050 has 4GB VRAM, which is sufficient for CLIP ViT-B/32 model
- GPU will automatically be used for embedding generation
- The config.yaml already has `device: "cuda"` set with auto-fallback to CPU
- No code changes needed - just reinstall PyTorch with CUDA support
