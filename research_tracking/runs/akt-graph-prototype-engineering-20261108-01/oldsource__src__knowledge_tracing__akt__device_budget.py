"""Giới hạn PyTorch CUDA allocator cho synthetic smoke, không là bill/driver cap."""


def configure_cuda_budget(cuda, *, max_vram_bytes):
    if (type(max_vram_bytes) is not int or not 64*1024**2<=max_vram_bytes<=2*1024**3):
        raise ValueError('invalid CUDA allocator budget')
    if cuda.is_available() is not True:
        raise ValueError('CUDA smoke cannot fall back to CPU')
    count=cuda.device_count()
    if type(count) is not int or count!=1:raise ValueError('CUDA smoke requires exactly one visible device')
    total=cuda.get_device_properties(0).total_memory
    if type(total) is not int or total<max_vram_bytes:raise ValueError('GPU memory below approved allocator budget')
    cuda.set_per_process_memory_fraction(max_vram_bytes/total,0)
    cuda.reset_peak_memory_stats(0)
    return {'device_index':0,'visible_devices':count,'total_device_memory_bytes':total,
            'max_vram_bytes':max_vram_bytes,'gpu_name':cuda.get_device_name(0),
            'scope':'PyTorch allocator only; not total driver memory or cloud billing limit'}


def cuda_budget_snapshot(cuda, *, max_vram_bytes):
    result={name:getattr(cuda,name)(0) for name in ('memory_allocated','memory_reserved',
                                                   'max_memory_allocated','max_memory_reserved')}
    if any(type(v) is not int or v<0 for v in result.values()):raise ValueError('invalid CUDA telemetry')
    if max(result.values())>max_vram_bytes:raise MemoryError('CUDA allocator budget exceeded')
    return result
