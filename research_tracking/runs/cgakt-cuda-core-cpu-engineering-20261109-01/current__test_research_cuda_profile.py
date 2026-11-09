"""Recipe28 metadata only; imports config through the real package, no CUDA/model."""
from dataclasses import FrozenInstanceError, asdict, fields, replace
import json
import unittest

from knowledge_tracing.akt.config import AKTConfig, PROJECT_ROOT, ResearchCUDAExecutionProfile, validate_config


def research_config():
    return AKTConfig(phase='simulator-research',run_id='cuda-profile-metadata-no-output',
        output_dir=PROJECT_ROOT/'experiments/akt/results/cuda-profile-metadata-no-output',
        max_train_users=8,max_val_users=1,max_targets_per_side=100,max_total_targets=200,
        max_steps=3,max_seconds=60.,max_wall_seconds=90.,max_rss_bytes=1024**3,min_available_ram_bytes=1024**3)


class ResearchCUDAProfileTests(unittest.TestCase):
    def test_profile_exact_recipe_and_json_metadata(self):
        profile=ResearchCUDAExecutionProfile(max_vram_bytes=1024**3)
        self.assertEqual(json.loads(json.dumps(asdict(profile))),asdict(profile))
        self.assertEqual((profile.recipe_id,profile.device,profile.seed,profile.dtype),
                         ('cgakt-cuda-fp32-v1','cuda:0',42,'float32'))
        self.assertEqual(profile.clip_foreach,'native-default-None')
        self.assertEqual(profile.initialization,'cpu-default-generator-42-then-device')
        self.assertFalse(any(getattr(profile,key) for key in ('foreach','fused','capturable','differentiable',
            'amsgrad','maximize','decoupled_weight_decay','deterministic_warn_only',
            'matmul_allow_tf32','cudnn_allow_tf32','cudnn_benchmark')))
        self.assertTrue(profile.deterministic_algorithms)
        self.assertEqual(profile.matmul_precision,'highest')
        self.assertEqual(profile.cublas_workspace_config,':4096:8')

    def test_profile_budget_is_explicit_and_bounded(self):
        with self.assertRaises(TypeError):ResearchCUDAExecutionProfile()
        for cap in (64*1024**2,2*1024**3):
            with self.subTest(cap=cap):self.assertEqual(ResearchCUDAExecutionProfile(cap).max_vram_bytes,cap)
        for cap in (None,True,0,64*1024**2-1,2*1024**3+1,1.,'1073741824'):
            with self.subTest(cap=cap),self.assertRaises(ValueError):ResearchCUDAExecutionProfile(cap)

    def test_profile_rejects_every_changed_fixed_field(self):
        profile=ResearchCUDAExecutionProfile(1024**3)
        for item in fields(profile):
            if item.name=='max_vram_bytes':continue
            value=getattr(profile,item.name)
            changed=not value if type(value) is bool else value+1 if type(value) is int else value+'-different'
            with self.subTest(field=item.name),self.assertRaises(ValueError):replace(profile,**{item.name:changed})

    def test_boolean_flags_and_seed_do_not_accept_numeric_aliases(self):
        profile=ResearchCUDAExecutionProfile(1024**3)
        for key in ('foreach','fused','capturable','differentiable','amsgrad','maximize',
                    'decoupled_weight_decay','deterministic_algorithms','deterministic_warn_only',
                    'matmul_allow_tf32','cudnn_allow_tf32','cudnn_benchmark'):
            with self.subTest(field=key),self.assertRaises(ValueError):replace(profile,**{key:int(getattr(profile,key))})
        with self.assertRaises(ValueError):replace(profile,seed=42.)

    def test_profile_is_frozen_and_backdoor_drift_revalidated(self):
        profile=ResearchCUDAExecutionProfile(1024**3)
        with self.assertRaises(FrozenInstanceError):profile.fused=True
        object.__setattr__(profile,'fused',True)
        with self.assertRaises(ValueError):validate_config(replace(research_config(),device='cuda'),cuda_profile=profile)

    def test_akt_config_field_population_is_unchanged(self):
        expected=('project_root','output_dir','phase','run_id','execution_enabled','partition','graph',
            'source_commit','source_root','outer_fold','device','seed','context','target_block','max_length',
            'd_model','heads','blocks','d_ff','final_fc','dropout','kq_same','separate_qa','n_pid','batch_size',
            'lr','betas','eps','weight_decay','max_grad_norm','inner_val_fraction','min_delta','patience',
            'max_epochs','max_train_users','max_val_users','max_targets_per_side','max_total_targets','max_steps',
            'max_seconds','max_wall_seconds','max_rss_bytes','min_available_ram_bytes','protocol_version',
            'memory_mb','threads','fetch_rows','recovery')
        self.assertEqual(tuple(item.name for item in fields(AKTConfig)),expected)
        self.assertNotIn('cuda_profile',asdict(AKTConfig()))

    def test_cpu_default_validation_and_serialization_unchanged(self):
        config=research_config();before=asdict(config)
        self.assertIsNone(validate_config(config))
        self.assertIsNone(validate_config(config,cuda_profile=None))
        self.assertEqual(asdict(config),before)
        self.assertEqual((config.device,config.seed,config.context,config.target_block,config.d_model,config.lr),
                         ('cpu',42,100,100,256,1e-4))

    def test_cuda_research_default_remains_rejected(self):
        config=replace(research_config(),device='cuda')
        with self.assertRaises(ValueError):validate_config(config)
        with self.assertRaises(ValueError):validate_config(config,cuda_profile=None)

    def test_cuda_research_requires_exact_typed_profile(self):
        config=replace(research_config(),device='cuda')
        profile=ResearchCUDAExecutionProfile(1024**3)
        self.assertIsNone(validate_config(config,cuda_profile=profile))  # Metadata acceptance, not actual GPU proof.
        for value in (True,{},asdict(profile),object()):
            with self.subTest(profile=type(value).__name__),self.assertRaises(ValueError):
                validate_config(config,cuda_profile=value)
        class Derived(ResearchCUDAExecutionProfile):pass
        with self.assertRaises(ValueError):validate_config(config,cuda_profile=Derived(1024**3))

    def test_cuda_profile_cannot_be_passed_positionally(self):
        with self.assertRaises(TypeError):validate_config(replace(research_config(),device='cuda'),ResearchCUDAExecutionProfile(1024**3))

    def test_profile_cannot_change_cpu_or_unrelated_phase_authority(self):
        profile=ResearchCUDAExecutionProfile(1024**3)
        for config in (research_config(),AKTConfig(),replace(research_config(),phase='cuda-smoke',device='cuda'),
                       replace(research_config(),phase='pilot',device='cuda')):
            with self.subTest(phase=config.phase,device=config.device),self.assertRaises(ValueError):
                validate_config(config,cuda_profile=profile)

    def test_cuda_profile_does_not_change_frozen_scientific_recipe(self):
        profile=ResearchCUDAExecutionProfile(1024**3);base=replace(research_config(),device='cuda')
        changes={'seed':43,'context':99,'target_block':99,'d_model':128,'heads':4,'dropout':.1,
                 'batch_size':2,'lr':2e-4,'betas':(.8,.999),'eps':1e-7,'weight_decay':.01,
                 'max_grad_norm':2.,'max_epochs':19,'patience':2,'min_delta':.001,'outer_fold':1}
        for name,value in changes.items():
            with self.subTest(field=name),self.assertRaises(ValueError):
                validate_config(replace(base,**{name:value}),cuda_profile=profile)

    def test_cuda_profile_does_not_override_resource_caps(self):
        profile=ResearchCUDAExecutionProfile(1024**3);base=replace(research_config(),device='cuda')
        for changes in ({'max_steps':None},{'max_steps':True},{'max_seconds':float('nan')},
                        {'max_seconds':91.},{'min_available_ram_bytes':0}):
            with self.subTest(changes=changes),self.assertRaises(ValueError):
                validate_config(replace(base,**changes),cuda_profile=profile)


if __name__=='__main__':unittest.main()
