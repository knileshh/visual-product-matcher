# Performance Benchmarks - Visual Product Matcher

## System Specifications
- **GPU**: NVIDIA GeForce RTX 3050 Laptop GPU (4GB VRAM)
- **CPU**: [Your CPU model]
- **Dataset**: 42,700 fashion images (jpg format)
- **Model**: CLIP ViT-B/32 (512-dimensional embeddings)
- **Framework**: PyTorch 2.8.0 with CUDA 12.6

---

## Initial Run (CPU Only - October 14, 2025)

### Configuration
- PyTorch: 2.1.0+cpu
- Batch Size: 32
- Device: CPU

### Performance
| Phase | Time | Rate |
|-------|------|------|
| Database Population | ~8 min | ~89 products/sec |
| Embedding Generation | ~16 min | ~89 images/sec |
| FAISS Index Building | <1 sec | - |
| **Total** | **~24 min** | - |

### Issues
- Duplicate image counting (85,400 instead of 42,700 due to case-insensitive pattern matching)
- CPU-only processing (CUDA not available)

---

## Optimized Run #1 (GPU - October 14, 2025)

### Configuration
- PyTorch: 2.8.0+cu126
- Batch Size: 32
- Device: CUDA (RTX 3050)

### Performance
| Phase | Time | Rate |
|-------|------|------|
| Database Population | 5:49 | ~122 products/sec |
| Embedding Generation | 3:22 | **~211 images/sec** |
| FAISS Index Building | <1 sec | - |
| **Total** | **~9:11 min** | - |

### Improvements
✅ Fixed duplicate image counting bug (using set deduplication)  
✅ Enabled GPU acceleration with CUDA 12.6  
✅ **2.37x speedup** on embedding generation vs CPU  
✅ **62% reduction** in total processing time

### GPU Utilization
- **Not fully utilized** at batch_size=32
- GPU memory usage: ~1.5-2GB out of 4GB available
- Potential for further optimization

---

## Future Optimization Opportunities

### 1. Increase Batch Size
**Current**: 32 → **Recommended**: 128-256

Expected improvements:
- Better GPU core utilization (parallel processing)
- Reduced data transfer overhead
- **Estimated speedup**: 1.5-2x additional improvement
- **Target rate**: 350-400+ images/sec

**Risk**: May hit VRAM limits if batch too large
**Mitigation**: Gradually increase (64 → 96 → 128 → 256) until CUDA OOM error

### 2. Mixed Precision Training (FP16)
```python
# Enable in embedding_service.py
with torch.cuda.amp.autocast():
    features = model.encode_image(images)
```

Expected improvements:
- **20-30% speedup** with minimal accuracy loss
- Reduced VRAM usage (allows larger batches)

### 3. Multi-GPU Support (if available)
- Use `torch.nn.DataParallel` or `torch.nn.parallel.DistributedDataParallel`
- Near-linear scaling with additional GPUs

### 4. Image Preprocessing Optimization
- Pre-resize images to CLIP's expected size (224x224)
- Use faster image loading libraries (turbojpeg, pillow-simd)
- Batch image loading with multiprocessing

### 5. Database Optimization
- Use batch inserts instead of individual inserts
- Create indexes on frequently queried columns
- Consider PostgreSQL for production (faster than SQLite)

---

## Performance Comparison Table

| Configuration | Total Time | Embedding Rate | Speedup |
|--------------|-----------|---------------|---------|
| CPU (batch=32) | ~24 min | 89 img/sec | 1.0x baseline |
| GPU (batch=32) | 9:11 min | 211 img/sec | **2.37x** |
| GPU (batch=128, estimated) | ~5-6 min | 350-400 img/sec | **4.0-4.5x** |
| GPU (batch=128 + FP16, estimated) | ~4-5 min | 450-500 img/sec | **5.0-5.6x** |

---

## Recommendations

### For Development (Current Setup)
✅ **batch_size: 128** - Good balance of speed and stability  
✅ Keep current PyTorch 2.8.0+cu126 setup  
✅ Monitor GPU usage with `nvidia-smi` during runs

### For Production
- Increase batch_size to 256 if no CUDA OOM errors
- Enable mixed precision (FP16) for 20-30% additional speedup
- Pre-process images offline to speed up initial indexing
- Use PostgreSQL instead of SQLite for better concurrency
- Consider caching embeddings for frequently searched images

### Testing Next Optimization
To test batch_size=128 performance:
```powershell
# Clean existing data
Remove-Item data/products.db, data/embeddings, data/index -Recurse -Force

# Run with new batch size
python init_data.py

# Monitor GPU usage in another terminal
nvidia-smi -l 1
```

Expected result: **~5-6 minutes total**, **350-400 images/sec** during embedding generation

---

## Monitoring Commands

### Check GPU Usage
```powershell
# Real-time monitoring (updates every 1 second)
nvidia-smi -l 1

# Single snapshot
nvidia-smi
```

### Check PyTorch GPU Setup
```powershell
python -c "import torch; print('CUDA:', torch.cuda.is_available()); print('GPU:', torch.cuda.get_device_name(0))"
```

### Profile Memory Usage
```powershell
# During init_data.py run
nvidia-smi --query-gpu=memory.used,memory.total --format=csv -l 1
```

---

## Notes

- Database population is I/O bound, not affected by GPU batch size
- Embedding generation benefits most from GPU optimization
- FAISS index building is very fast regardless of configuration
- RTX 3050 4GB can handle batch sizes up to ~256 for CLIP ViT-B/32
- Larger CLIP models (ViT-L/14) would require smaller batch sizes
