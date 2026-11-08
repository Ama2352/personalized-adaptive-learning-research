"""Chặn model/optimizer thật trong callback fixture suite."""
import sys
import torch
import pytest
import knowledge_tracing.akt.upstream as upstream
import knowledge_tracing.akt.model as model


def forbidden(*args, **kwargs):
    raise AssertionError('No native constructor/Adam step in pure suite')


torch.set_num_threads(2)
upstream.build_native=forbidden
model.build_native=forbidden
model.AKTAdapter.__init__=forbidden
torch.optim.Adam.step=forbidden
print('NO_MODEL_SPIES_INSTALLED',flush=True)
raise SystemExit(pytest.main(sys.argv[1:]))
