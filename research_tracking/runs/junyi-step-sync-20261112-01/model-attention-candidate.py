"""Adapter AKT NonRasch, predict nhân quả và training loss theo target."""

from collections.abc import Sequence
import time

import numpy as np
import torch

from knowledge_tracing.shared_kt import CausalSequenceInputs
from .config import AKTConfig
from .encoding import ExerciseEncoding
from .tensors import AKTBatch, collate_windows
from .types import WindowInputs, WindowSlice
from .upstream import build_native
from .windows import iter_window_slices, slice_causal_inputs


class AKTAdapter:
    def __init__(self, config: AKTConfig, encoding: ExerciseEncoding):
        self.config = config
        self.encoding = encoding
        self.native = build_native(config, n_items=len(encoding.vocabulary.values))

    def step(self, batch: AKTBatch, optimizer: torch.optim.Optimizer) -> dict:
        from attention_candidate import install
        if not getattr(self, '_attention_device_cast_installed', False):
            install(self)
            self._attention_device_cast_installed = True
        if not torch.isin(batch.loss_targets, torch.tensor([-1., 0., 1.], device=batch.loss_targets.device)).all():
            raise ValueError('invalid loss target values')
        valid_targets = batch.loss_targets >= 0
        expected = batch.target_mask & batch.valid_mask
        if torch.any(valid_targets & ~expected) or torch.any(batch.loss_targets > 1):
            raise ValueError('invalid loss target mask')
        n = int(valid_targets.sum().item())
        optimizer.zero_grad(set_to_none=True)
        if n == 0:
            return {'stepped': False, 'valid_targets': 0, 'mean_loss': None,
                    'forward_seconds': 0.0, 'backward_seconds': 0.0,
                    'gradient_clip_seconds': 0.0, 'optimizer_seconds': 0.0}
        forward_started = time.perf_counter()
        loss, predictions, count = self.native(batch.q_data, batch.qa_data, batch.loss_targets)
        forward_seconds = time.perf_counter() - forward_started
        if int(count.item()) != n or not torch.isfinite(loss) or not torch.isfinite(predictions).all():
            raise ValueError('nonfinite output or inconsistent loss mask')
        mean_loss = loss / n
        backward_started = time.perf_counter()
        mean_loss.backward()
        backward_seconds = time.perf_counter() - backward_started
        clip_started = time.perf_counter()
        norm = torch.nn.utils.clip_grad_norm_(self.native.parameters(), self.config.max_grad_norm,
                                             error_if_nonfinite=True)
        gradient_clip_seconds = time.perf_counter() - clip_started
        probe = None
        for parameter in self.native.parameters():
            if parameter.grad is not None and torch.any(parameter.grad != 0):
                index = int(parameter.grad.detach().abs().reshape(-1).argmax().item())
                flat_parameter = parameter.detach().reshape(-1)
                probe = (flat_parameter, index, float(flat_parameter[index].item()))
                break
        optimizer_started = time.perf_counter()
        optimizer.step()
        optimizer_seconds = time.perf_counter() - optimizer_started
        parameter_updated = bool(probe is not None and float(probe[0][probe[1]].item()) != probe[2])
        return {'stepped': True, 'valid_targets': n, 'loss_sum': float(loss.detach().item()),
                'mean_loss': float(mean_loss.detach().item()), 'pre_clip_norm': float(norm.item()),
                'post_clip_norm': min(float(norm.item()), self.config.max_grad_norm),
                'parameter_updated': parameter_updated,
                'forward_seconds': forward_seconds, 'backward_seconds': backward_seconds,
                'gradient_clip_seconds': gradient_clip_seconds,
                'optimizer_seconds': optimizer_seconds}

    def fit(self, inputs: CausalSequenceInputs, targets: np.ndarray) -> 'AKTAdapter':
        labels = np.asarray(targets)
        if labels.shape != inputs.item_ids.shape or not np.isin(labels, (0, 1)).all():
            raise ValueError('invalid training targets')
        if np.any(inputs.item_ids < 0) or np.any(inputs.item_ids >= len(self.encoding.vocabulary.values)):
            raise ValueError('training scope contains unseen exercise')
        optimizer = torch.optim.Adam(self.native.parameters(), lr=self.config.lr,
                                     betas=self.config.betas, eps=self.config.eps,
                                     weight_decay=self.config.weight_decay)
        self.native.train()
        windows: list[WindowInputs] = []
        window_targets: list[np.ndarray] = []

        def flush() -> None:
            if windows:
                batch = collate_windows(windows, n_items=len(self.encoding.vocabulary.values),
                                        device=self.config.device, targets=window_targets)
                self.step(batch, optimizer)
                windows.clear()
                window_targets.clear()

        for geometry in iter_window_slices(inputs.item_ids, inputs.sequence_offsets,
                                           context=self.config.context, target_block=self.config.target_block):
            if geometry.unseen:
                raise ValueError('training scope contains unseen exercise')
            windows.append(slice_causal_inputs(inputs, geometry))
            window_targets.append(labels[geometry.start:geometry.stop])
            if len(windows) >= self.config.batch_size:
                flush()
        flush()
        return self

    def predict_window(self, window: WindowInputs) -> np.ndarray:
        """Chấm một window đã có global geometry, không cắt/re-anchor lần nữa."""
        return self.predict_windows([window])[0]

    def predict_windows(self, windows: Sequence[WindowInputs]) -> list[np.ndarray]:
        """Batch các window độc lập, không vượt batch_size đã cấu hình."""
        for window in windows:
            size = len(window.inputs.item_ids)
            if (not 1 <= size <= self.config.max_length or len(window.inputs.user_ids) != size
                    or len(set(window.inputs.user_ids)) != 1
                    or not np.array_equal(window.inputs.sequence_offsets, [0, size])):
                raise ValueError('invalid prebuilt prediction window')
        previous_mode = self.native.training
        output = []
        try:
            self.native.eval()
            with torch.no_grad():
                for start in range(0, len(windows), self.config.batch_size):
                    group = windows[start:start+self.config.batch_size]
                    batch = collate_windows(group, n_items=len(self.encoding.vocabulary.values), device=self.config.device)
                    _, probabilities, _ = self.native(batch.q_data, batch.qa_data, batch.loss_targets)
                    result = probabilities.reshape(batch.q_data.shape).cpu().numpy().astype(np.float64)
                    if not np.isfinite(result).all() or np.any((result < 0) | (result > 1)):
                        raise ValueError('invalid prebuilt window probabilities')
                    output.extend(result[index,:len(window.inputs.item_ids)].copy() for index,window in enumerate(group))
            return output
        finally:
            self.native.train(previous_mode)

    def predict(self, inputs: CausalSequenceInputs) -> np.ndarray:
        result = np.full(len(inputs.item_ids), np.nan, dtype=np.float64)
        visited = np.zeros(len(result), dtype=bool)
        pending: list[tuple[WindowSlice, WindowInputs]] = []
        previous_mode = self.native.training
        self.native.eval()

        def flush() -> None:
            if not pending:
                return
            windows = [window for _, window in pending]
            batch = collate_windows(windows, n_items=len(self.encoding.vocabulary.values), device=self.config.device)
            _, probabilities, _ = self.native(batch.q_data, batch.qa_data, batch.loss_targets)
            probabilities = probabilities.reshape(batch.q_data.shape).cpu().numpy()
            for row, (geometry, window) in enumerate(pending):
                indexes = np.arange(geometry.start, geometry.stop)[window.target_mask]
                values = probabilities[row, :geometry.stop-geometry.start][window.target_mask]
                if visited[indexes].any() or not np.isfinite(values).all():
                    raise ValueError('duplicate or nonfinite predictions')
                result[indexes] = values
                visited[indexes] = True
            pending.clear()

        try:
            with torch.no_grad():
                for geometry in iter_window_slices(inputs.item_ids, inputs.sequence_offsets,
                                                   context=self.config.context, target_block=self.config.target_block):
                    if geometry.unseen:
                        if visited[geometry.start]:
                            raise ValueError('duplicate prediction row')
                        visited[geometry.start] = True
                    else:
                        pending.append((geometry, slice_causal_inputs(inputs, geometry)))
                        if len(pending) >= self.config.batch_size:
                            flush()
                flush()
        finally:
            self.native.train(previous_mode)
        if not visited.all():
            raise ValueError('missing prediction row')
        return result
