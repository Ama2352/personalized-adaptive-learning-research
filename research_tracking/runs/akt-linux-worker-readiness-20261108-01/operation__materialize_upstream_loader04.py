"""OFFLINE v04 transferred blob: pin-format remediation; parent review trước dispatch.

Chỉ Git thật tại checkout đã có. Không clone/fetch/network/optimizer/model/Gate.
Nguồn LOCAL_PINNED_GIT_BLOB_TRANSFER; Git object thật, không dựng commit/tree metadata.
Không sửa3source cũ, network/fetch/head rewrite hoặc relabel FAILED Gate23/cachemiss01.
"""
import argparse
import base64
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import re
import runpy
import shutil
import subprocess
import sys
import time
import traceback

ROOT=Path('/content/KLTN_GPU08_20261108_01')
UPSTREAM=ROOT/'artifacts/akt/dependencies/upstream'
STAGE=ROOT/'upstream-loader-transfer03'
PIN='01b7e8d7d7c862cabc9467108e3e7f2555653a88'
TREE='904863502337ef2eefd1769d14836b62e3c3804a'
URL='https://github.com/arghosh/AKT.git'
LOADER_SHA='27550ccd07c1131971c4381f024c0f3795dba3d32b7f9fb4eea4ababd8bfe9e8'
LOADER_BLOB='9fafe965e0b442242125250f37dc8c3f8a145edf'
LOCAL_LOADER_PROFILE_SHA='fe92be5208b9b2b1ba041945c7a5c190c0eef13a34679203c5f76acc93a8088e'
LOADER_BASE64='IyBDb2RlIHJldXNlZCBmcm9tIGh0dHBzOi8vZ2l0aHViLmNvbS9qZW5ueXpoYW5nMDIxNS9ES1ZNTi5naXQKaW1wb3J0IG51bXB5IGFzIG5wCmltcG9ydCBtYXRoCgoKY2xhc3MgREFUQShvYmplY3QpOgogICAgZGVmIF9faW5pdF9fKHNlbGYsIG5fcXVlc3Rpb24sIHNlcWxlbiwgc2VwYXJhdGVfY2hhciwgbmFtZT0iZGF0YSIpOgogICAgICAgICMgSW4gdGhlIEFTU0lTVG1lbnRzMjAwOSBkYXRhc2V0OgogICAgICAgICMgcGFyYW06IG5fcXVlYXRpb24gPSAxMTAKICAgICAgICAjICAgICAgICBzZXFsZW4gPSAyMDAKICAgICAgICBzZWxmLnNlcGFyYXRlX2NoYXIgPSBzZXBhcmF0ZV9jaGFyCiAgICAgICAgc2VsZi5uX3F1ZXN0aW9uID0gbl9xdWVzdGlvbgogICAgICAgIHNlbGYuc2VxbGVuID0gc2VxbGVuCiAgICAjIGRhdGEgZm9ybWF0CiAgICAjIGlkLCB0cnVlX3N0dWRlbnRfaWQKICAgICMgMSwxLDEsMSw3LDcsOSwxMCwxMCwxMCwxMCwxMSwxMSw0NSw1NAogICAgIyAwLDEsMSwxLDEsMSwwLDAsMSwxLDEsMSwxLDAsMAoKICAgIGRlZiBsb2FkX2RhdGEoc2VsZiwgcGF0aCk6CiAgICAgICAgZl9kYXRhID0gb3BlbihwYXRoLCAncicpCiAgICAgICAgcV9kYXRhID0gW10KICAgICAgICBxYV9kYXRhID0gW10KICAgICAgICBpZHhfZGF0YSA9IFtdCiAgICAgICAgZm9yIGxpbmVJRCwgbGluZSBpbiBlbnVtZXJhdGUoZl9kYXRhKToKICAgICAgICAgICAgbGluZSA9IGxpbmUuc3RyaXAoKQogICAgICAgICAgICAjIGxpbmVJRCBzdGFydHMgZnJvbSAwCiAgICAgICAgICAgIGlmIGxpbmVJRCAlIDMgPT0gMDoKICAgICAgICAgICAgICAgIHN0dWRlbnRfaWQgPSBsaW5lSUQvLzMKICAgICAgICAgICAgaWYgbGluZUlEICUgMyA9PSAxOgogICAgICAgICAgICAgICAgUSA9IGxpbmUuc3BsaXQoc2VsZi5zZXBhcmF0ZV9jaGFyKQogICAgICAgICAgICAgICAgaWYgbGVuKFFbbGVuKFEpLTFdKSA9PSAwOgogICAgICAgICAgICAgICAgICAgIFEgPSBRWzotMV0KICAgICAgICAgICAgICAgICMgcHJpbnQobGVuKFEpKQogICAgICAgICAgICBlbGlmIGxpbmVJRCAlIDMgPT0gMjoKICAgICAgICAgICAgICAgIEEgPSBsaW5lLnNwbGl0KHNlbGYuc2VwYXJhdGVfY2hhcikKICAgICAgICAgICAgICAgIGlmIGxlbihBW2xlbihBKS0xXSkgPT0gMDoKICAgICAgICAgICAgICAgICAgICBBID0gQVs6LTFdCiAgICAgICAgICAgICAgICAjIHByaW50KGxlbihBKSxBKQoKICAgICAgICAgICAgICAgICMgc3RhcnQgc3BsaXQgdGhlIGRhdGEKICAgICAgICAgICAgICAgIG5fc3BsaXQgPSAxCiAgICAgICAgICAgICAgICAjIHByaW50KCdsZW4oUSk6JyxsZW4oUSkpCiAgICAgICAgICAgICAgICBpZiBsZW4oUSkgPiBzZWxmLnNlcWxlbjoKICAgICAgICAgICAgICAgICAgICBuX3NwbGl0ID0gbWF0aC5mbG9vcihsZW4oUSkgLyBzZWxmLnNlcWxlbikKICAgICAgICAgICAgICAgICAgICBpZiBsZW4oUSkgJSBzZWxmLnNlcWxlbjoKICAgICAgICAgICAgICAgICAgICAgICAgbl9zcGxpdCA9IG5fc3BsaXQgKyAxCiAgICAgICAgICAgICAgICAjIHByaW50KCduX3NwbGl0Oicsbl9zcGxpdCkKICAgICAgICAgICAgICAgIGZvciBrIGluIHJhbmdlKG5fc3BsaXQpOgogICAgICAgICAgICAgICAgICAgIHF1ZXN0aW9uX3NlcXVlbmNlID0gW10KICAgICAgICAgICAgICAgICAgICBhbnN3ZXJfc2VxdWVuY2UgPSBbXQogICAgICAgICAgICAgICAgICAgIGlmIGsgPT0gbl9zcGxpdCAtIDE6CiAgICAgICAgICAgICAgICAgICAgICAgIGVuZElOZGV4ID0gbGVuKEEpCiAgICAgICAgICAgICAgICAgICAgZWxzZToKICAgICAgICAgICAgICAgICAgICAgICAgZW5kSU5kZXggPSAoaysxKSAqIHNlbGYuc2VxbGVuCiAgICAgICAgICAgICAgICAgICAgZm9yIGkgaW4gcmFuZ2UoayAqIHNlbGYuc2VxbGVuLCBlbmRJTmRleCk6CiAgICAgICAgICAgICAgICAgICAgICAgIGlmIGxlbihRW2ldKSA+IDA6CiAgICAgICAgICAgICAgICAgICAgICAgICAgICAjIGludChBW2ldKSBpcyBpbiB7MCwxfQogICAgICAgICAgICAgICAgICAgICAgICAgICAgWGluZGV4ID0gaW50KFFbaV0pICsgaW50KEFbaV0pICogc2VsZi5uX3F1ZXN0aW9uCiAgICAgICAgICAgICAgICAgICAgICAgICAgICBxdWVzdGlvbl9zZXF1ZW5jZS5hcHBlbmQoaW50KFFbaV0pKQogICAgICAgICAgICAgICAgICAgICAgICAgICAgYW5zd2VyX3NlcXVlbmNlLmFwcGVuZChYaW5kZXgpCiAgICAgICAgICAgICAgICAgICAgICAgIGVsc2U6CiAgICAgICAgICAgICAgICAgICAgICAgICAgICBwcmludChRW2ldKQogICAgICAgICAgICAgICAgICAgICNwcmludCgnaW5zdGFuY2U6LS0+JywgbGVuKGluc3RhbmNlKSxpbnN0YW5jZSkKICAgICAgICAgICAgICAgICAgICBxX2RhdGEuYXBwZW5kKHF1ZXN0aW9uX3NlcXVlbmNlKQogICAgICAgICAgICAgICAgICAgIHFhX2RhdGEuYXBwZW5kKGFuc3dlcl9zZXF1ZW5jZSkKICAgICAgICAgICAgICAgICAgICBpZHhfZGF0YS5hcHBlbmQoc3R1ZGVudF9pZCkKICAgICAgICBmX2RhdGEuY2xvc2UoKQogICAgICAgICMjIyBkYXRhOiBbW10sW10sW10sLi4uXSA8LS0gc2V0X21heF9zZXFsZW4gaXMgdXNlZAogICAgICAgICMgY29udmVydCBkYXRhIGludG8gbmRhcnJheXMgZm9yIGJldHRlciBzcGVlZCBkdXJpbmcgdHJhaW5pbmcKICAgICAgICBxX2RhdGFBcnJheSA9IG5wLnplcm9zKChsZW4ocV9kYXRhKSwgc2VsZi5zZXFsZW4pKQogICAgICAgIGZvciBqIGluIHJhbmdlKGxlbihxX2RhdGEpKToKICAgICAgICAgICAgZGF0ID0gcV9kYXRhW2pdCiAgICAgICAgICAgIHFfZGF0YUFycmF5W2osIDpsZW4oZGF0KV0gPSBkYXQKCiAgICAgICAgcWFfZGF0YUFycmF5ID0gbnAuemVyb3MoKGxlbihxYV9kYXRhKSwgc2VsZi5zZXFsZW4pKQogICAgICAgIGZvciBqIGluIHJhbmdlKGxlbihxYV9kYXRhKSk6CiAgICAgICAgICAgIGRhdCA9IHFhX2RhdGFbal0KICAgICAgICAgICAgcWFfZGF0YUFycmF5W2osIDpsZW4oZGF0KV0gPSBkYXQKICAgICAgICAjIGRhdGFBcnJheTogWyBhcnJheShbW10sW10sLi5dKV0gU2hhcGU6ICgzNjMzLCAyMDApCiAgICAgICAgcmV0dXJuIHFfZGF0YUFycmF5LCBxYV9kYXRhQXJyYXksIG5wLmFzYXJyYXkoaWR4X2RhdGEpCgoKY2xhc3MgUElEX0RBVEEob2JqZWN0KToKICAgIGRlZiBfX2luaXRfXyhzZWxmLCBuX3F1ZXN0aW9uLCAgc2VxbGVuLCBzZXBhcmF0ZV9jaGFyLCBuYW1lPSJkYXRhIik6CiAgICAgICAgIyBJbiB0aGUgQVNTSVNUbWVudHMyMDA5IGRhdGFzZXQ6CiAgICAgICAgIyBwYXJhbTogbl9xdWVhdGlvbiA9IDExMAogICAgICAgICMgICAgICAgIHNlcWxlbiA9IDIwMAogICAgICAgIHNlbGYuc2VwYXJhdGVfY2hhciA9IHNlcGFyYXRlX2NoYXIKICAgICAgICBzZWxmLnNlcWxlbiA9IHNlcWxlbgogICAgICAgIHNlbGYubl9xdWVzdGlvbiA9IG5fcXVlc3Rpb24KICAgICMgZGF0YSBmb3JtYXQKICAgICMgaWQsIHRydWVfc3R1ZGVudF9pZAogICAgIyBwaWQxLCBwaWQyLCAuLi4KICAgICMgMSwxLDEsMSw3LDcsOSwxMCwxMCwxMCwxMCwxMSwxMSw0NSw1NAogICAgIyAwLDEsMSwxLDEsMSwwLDAsMSwxLDEsMSwxLDAsMAoKICAgIGRlZiBsb2FkX2RhdGEoc2VsZiwgcGF0aCk6CiAgICAgICAgZl9kYXRhID0gb3BlbihwYXRoLCAncicpCiAgICAgICAgcV9kYXRhID0gW10KICAgICAgICBxYV9kYXRhID0gW10KICAgICAgICBwX2RhdGEgPSBbXQogICAgICAgIGZvciBsaW5lSUQsIGxpbmUgaW4gZW51bWVyYXRlKGZfZGF0YSk6CiAgICAgICAgICAgIGxpbmUgPSBsaW5lLnN0cmlwKCkKICAgICAgICAgICAgIyBsaW5lSUQgc3RhcnRzIGZyb20gMAogICAgICAgICAgICBpZiBsaW5lSUQgJSA0ID09IDA6CiAgICAgICAgICAgICAgICBzdHVkZW50X2lkID0gbGluZUlELy80CiAgICAgICAgICAgIGlmIGxpbmVJRCAlIDQgPT0gMjoKICAgICAgICAgICAgICAgIFEgPSBsaW5lLnNwbGl0KHNlbGYuc2VwYXJhdGVfY2hhcikKICAgICAgICAgICAgICAgIGlmIGxlbihRW2xlbihRKS0xXSkgPT0gMDoKICAgICAgICAgICAgICAgICAgICBRID0gUVs6LTFdCiAgICAgICAgICAgICAgICAjIHByaW50KGxlbihRKSkKICAgICAgICAgICAgaWYgbGluZUlEICUgNCA9PSAxOgogICAgICAgICAgICAgICAgUCA9IGxpbmUuc3BsaXQoc2VsZi5zZXBhcmF0ZV9jaGFyKQogICAgICAgICAgICAgICAgaWYgbGVuKFBbbGVuKFApIC0gMV0pID09IDA6CiAgICAgICAgICAgICAgICAgICAgUCA9IFBbOi0xXQoKICAgICAgICAgICAgZWxpZiBsaW5lSUQgJSA0ID09IDM6CiAgICAgICAgICAgICAgICBBID0gbGluZS5zcGxpdChzZWxmLnNlcGFyYXRlX2NoYXIpCiAgICAgICAgICAgICAgICBpZiBsZW4oQVtsZW4oQSktMV0pID09IDA6CiAgICAgICAgICAgICAgICAgICAgQSA9IEFbOi0xXQogICAgICAgICAgICAgICAgIyBwcmludChsZW4oQSksQSkKCiAgICAgICAgICAgICAgICAjIHN0YXJ0IHNwbGl0IHRoZSBkYXRhCiAgICAgICAgICAgICAgICBuX3NwbGl0ID0gMQogICAgICAgICAgICAgICAgIyBwcmludCgnbGVuKFEpOicsbGVuKFEpKQogICAgICAgICAgICAgICAgaWYgbGVuKFEpID4gc2VsZi5zZXFsZW46CiAgICAgICAgICAgICAgICAgICAgbl9zcGxpdCA9IG1hdGguZmxvb3IobGVuKFEpIC8gc2VsZi5zZXFsZW4pCiAgICAgICAgICAgICAgICAgICAgaWYgbGVuKFEpICUgc2VsZi5zZXFsZW46CiAgICAgICAgICAgICAgICAgICAgICAgIG5fc3BsaXQgPSBuX3NwbGl0ICsgMQogICAgICAgICAgICAgICAgIyBwcmludCgnbl9zcGxpdDonLG5fc3BsaXQpCiAgICAgICAgICAgICAgICBmb3IgayBpbiByYW5nZShuX3NwbGl0KToKICAgICAgICAgICAgICAgICAgICBxdWVzdGlvbl9zZXF1ZW5jZSA9IFtdCiAgICAgICAgICAgICAgICAgICAgcHJvYmxlbV9zZXF1ZW5jZSA9IFtdCiAgICAgICAgICAgICAgICAgICAgYW5zd2VyX3NlcXVlbmNlID0gW10KICAgICAgICAgICAgICAgICAgICBpZiBrID09IG5fc3BsaXQgLSAxOgogICAgICAgICAgICAgICAgICAgICAgICBlbmRJTmRleCA9IGxlbihBKQogICAgICAgICAgICAgICAgICAgIGVsc2U6CiAgICAgICAgICAgICAgICAgICAgICAgIGVuZElOZGV4ID0gKGsrMSkgKiBzZWxmLnNlcWxlbgogICAgICAgICAgICAgICAgICAgIGZvciBpIGluIHJhbmdlKGsgKiBzZWxmLnNlcWxlbiwgZW5kSU5kZXgpOgogICAgICAgICAgICAgICAgICAgICAgICBpZiBsZW4oUVtpXSkgPiAwOgogICAgICAgICAgICAgICAgICAgICAgICAgICAgWGluZGV4ID0gaW50KFFbaV0pICsgaW50KEFbaV0pICogc2VsZi5uX3F1ZXN0aW9uCiAgICAgICAgICAgICAgICAgICAgICAgICAgICBxdWVzdGlvbl9zZXF1ZW5jZS5hcHBlbmQoaW50KFFbaV0pKQogICAgICAgICAgICAgICAgICAgICAgICAgICAgcHJvYmxlbV9zZXF1ZW5jZS5hcHBlbmQoaW50KFBbaV0pKQogICAgICAgICAgICAgICAgICAgICAgICAgICAgYW5zd2VyX3NlcXVlbmNlLmFwcGVuZChYaW5kZXgpCiAgICAgICAgICAgICAgICAgICAgICAgIGVsc2U6CiAgICAgICAgICAgICAgICAgICAgICAgICAgICBwcmludChRW2ldKQogICAgICAgICAgICAgICAgICAgIHFfZGF0YS5hcHBlbmQocXVlc3Rpb25fc2VxdWVuY2UpCiAgICAgICAgICAgICAgICAgICAgcWFfZGF0YS5hcHBlbmQoYW5zd2VyX3NlcXVlbmNlKQogICAgICAgICAgICAgICAgICAgIHBfZGF0YS5hcHBlbmQocHJvYmxlbV9zZXF1ZW5jZSkKCiAgICAgICAgZl9kYXRhLmNsb3NlKCkKICAgICAgICAjIyMgZGF0YTogW1tdLFtdLFtdLC4uLl0gPC0tIHNldF9tYXhfc2VxbGVuIGlzIHVzZWQKICAgICAgICAjIGNvbnZlcnQgZGF0YSBpbnRvIG5kYXJyYXlzIGZvciBiZXR0ZXIgc3BlZWQgZHVyaW5nIHRyYWluaW5nCiAgICAgICAgcV9kYXRhQXJyYXkgPSBucC56ZXJvcygobGVuKHFfZGF0YSksIHNlbGYuc2VxbGVuKSkKICAgICAgICBmb3IgaiBpbiByYW5nZShsZW4ocV9kYXRhKSk6CiAgICAgICAgICAgIGRhdCA9IHFfZGF0YVtqXQogICAgICAgICAgICBxX2RhdGFBcnJheVtqLCA6bGVuKGRhdCldID0gZGF0CgogICAgICAgIHFhX2RhdGFBcnJheSA9IG5wLnplcm9zKChsZW4ocWFfZGF0YSksIHNlbGYuc2VxbGVuKSkKICAgICAgICBmb3IgaiBpbiByYW5nZShsZW4ocWFfZGF0YSkpOgogICAgICAgICAgICBkYXQgPSBxYV9kYXRhW2pdCiAgICAgICAgICAgIHFhX2RhdGFBcnJheVtqLCA6bGVuKGRhdCldID0gZGF0CgogICAgICAgIHBfZGF0YUFycmF5ID0gbnAuemVyb3MoKGxlbihwX2RhdGEpLCBzZWxmLnNlcWxlbikpCiAgICAgICAgZm9yIGogaW4gcmFuZ2UobGVuKHBfZGF0YSkpOgogICAgICAgICAgICBkYXQgPSBwX2RhdGFbal0KICAgICAgICAgICAgcF9kYXRhQXJyYXlbaiwgOmxlbihkYXQpXSA9IGRhdAogICAgICAgIHJldHVybiBxX2RhdGFBcnJheSwgcWFfZGF0YUFycmF5LCBwX2RhdGFBcnJheQo='
PROFILE_BASE64='ew0KICAic3RhdHVzIjogIkxPQ0FMX1BJTk5FRF9HSVRfQkxPQl9ERVJJVkVEX05PVF9SRU1PVEVfTUFURVJJQUxJWkFUSU9OIiwNCiAgImNvbW1pdCI6ICIwMWI3ZThkN2Q3Yzg2MmNhYmM5NDY3MTA4ZTNlN2YyNTU1NjUzYTg4IiwNCiAgInBhdGgiOiAibG9hZF9kYXRhLnB5IiwNCiAgImdpdF9ibG9iX2lkIjogIjlmYWZlOTY1ZTBiNDQyMjQyMTI1MjUwZjM3ZGM4YzNmOGExNDVlZGYiLA0KICAic2hhMjU2IjogIjI3NTUwY2NkMDdjMTEzMTk3MWM0MzgxZjAyNGMwZjM3OTVkYmEzZDMyYjdmOWZiNGVlYTRhYmFiZDhiZmU5ZTgiLA0KICAiYnl0ZXMiOiA2NDI4LA0KICAiYXN0X3BhcnNlIjogdHJ1ZSwNCiAgInNvdXJjZV9vcl9tb2RlbF9leGVjdXRlZCI6IGZhbHNlDQp9'
LF={'akt.py':'ace9e4486ea6d8f8c52310a8ddf27212022136eda719c12d8204fab1bfcfdc67',
    'README.md':'bec19014f10f469002e46f53175a1599b1be9b2d3fc9fe184129e6da1efd442b',
    'LICENSE':'50a2c2d2521182935c537a56220083c7a4194abdfbd459b6c682fae32cceb4cf'}
PINS={'materialize_cached_upstream_loader01.py': '43526ab61ea51576b73a29126775a154533bedbdc830170990e03136916b596c', 'upstream-loader-cache01/result.json': 'c0f3a05bfd51ab0957c57f3957b163e3e88223fe3549104128e7329c1de8d80a', 'upstream-loader-cache01/output-manifest.json': '86ecc40514f2514e064290b0b98f46504b46cee93fb685e786369fb55af1b486', 'upstream_checkout01.py': 'f33c9d50dbde6a354c03c0f9d702f239a70a9d298f3ee0214718d0daadd9db90', 'upstream-checkout01/result.json': 'b82828207f763f53ca76d52827bbf1315a4cda7e403e8d1848b8cf9723732ca1', 'post-checkout-audit01/result.json': '1f116d3db2c88d2815bee73cb4471e56f6f442b744c4cd29cede7ce2a43cf952', 'linux-cpu-validation-gate-20261108-02/result.json': 'c7cf0a96ca75c32728fcb7d566d0f1fcac22b95ae940d6e37e916645081c6583', 'linux-cpu-validation-gate-20261108-02/output-manifest.json': '4edfac1ec01d910d92862c527d215400211d0e4f0729cb35904148514afe1224', 'materialize_upstream_loader03.py': '9489a25d14aab2f5ecd9173b128378db358c11950daa5aefcfd8615d2aabbda1', 'upstream-loader-transfer02/result.json': '8babe7655f6c545005e6f98ddb5c050cdfd850fd5552896c8001d5f9ed0538d9', 'upstream-loader-transfer02/output-manifest.json': 'a783cef946dd45bdcd9a23a9e42929cf4d78e4edf55fff5eafb268b0dfd6d7aa'}
def sha(raw):return hashlib.sha256(raw).hexdigest()
def validate_pin_inventory(values):
    if not isinstance(values,dict) or not values:raise ValueError('nonempty SHA pin inventory required')
    if any(not isinstance(v,str) or re.fullmatch('[a-f0-9]{64}',v) is None for v in values.values()):
        raise ValueError('every SHA pin must be exactly64 lowercase hex characters')
validate_pin_inventory(PINS) # Pure preflight, before any stage or Git mutation.
def validate_loader(raw,blob_id):
    actual=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
    if len(raw)!=6428 or sha(raw)!=LOADER_SHA or blob_id!=LOADER_BLOB or actual!=LOADER_BLOB:
        raise ValueError('cached loader size/SHA/Git blob identity mismatch')
def validate_original(identity,clean,raw):
    if identity!={'commit':PIN,'tree':TREE,'remote':URL,'files':LF} or clean:
        raise ValueError('pinned clean actual Git identity required')
    if set(raw)!=set(LF) or any(sha(raw[name])!=digest for name,digest in LF.items()):
        raise ValueError('original3LF source changed')
def isolated_environment(environment):
    env={k:v for k,v in environment.items() if not k.upper().startswith(('GIT_','GH_','GITHUB_','SSH_','PYTHON','PIP_','UV_','CONDA_'))
         and not any(s in k.upper() for s in ('TOKEN','SECRET','PASSWORD','CREDENTIAL','COOKIE','AUTH','API_KEY','PROXY'))
         and k not in {'HOME','XDG_CONFIG_HOME','LD_PRELOAD','LD_LIBRARY_PATH','CURL_HOME','NETRC'}}
    env.update(HOME=str(STAGE/'home'),XDG_CONFIG_HOME=str(STAGE/'home'),PATH='/usr/bin:/bin',
               GIT_CONFIG_NOSYSTEM='1',GIT_CONFIG_GLOBAL=os.devnull,GIT_TERMINAL_PROMPT='0',
               GIT_ALLOW_PROTOCOL='__NO_TRANSPORT__',GIT_OPTIONAL_LOCKS='0',GIT_NO_LAZY_FETCH='1',
               CUDA_VISIBLE_DEVICES='',NVIDIA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',
               GIT_CONFIG_COUNT='6',GIT_CONFIG_KEY_0='safe.directory',GIT_CONFIG_VALUE_0=UPSTREAM.as_posix(),
               GIT_CONFIG_KEY_1='core.hooksPath',GIT_CONFIG_VALUE_1=os.devnull,
               GIT_CONFIG_KEY_2='core.autocrlf',GIT_CONFIG_VALUE_2='false',
               GIT_CONFIG_KEY_3='credential.helper',GIT_CONFIG_VALUE_3='',
               GIT_CONFIG_KEY_4='credential.interactive',GIT_CONFIG_VALUE_4='false',
               GIT_CONFIG_KEY_5='core.fsmonitor',GIT_CONFIG_VALUE_5='false')
    return env

CHILD=r'''
import ast,hashlib,json,os,runpy,subprocess,sys,time
from pathlib import Path
profile=PROFILE_CONSTANTS
root=Path('/content/KLTN_GPU08_20261108_01');upstream=root/'artifacts/akt/dependencies/upstream';stage=root/'upstream-loader-transfer03'
sha=lambda raw:hashlib.sha256(raw).hexdigest()
helper=runpy.run_path(str(root/'upstream_checkout01.py'))
if (upstream/'.git').is_symlink() or not (upstream/'.git').is_dir():raise ValueError('existing physical legitimate clone metadata required')
before={name:helper['read_regular'](upstream/name) for name in profile['lf']}
kit_sha=helper['verify_kit']();started=time.monotonic();rows=[]
def git(*args,input_bytes=None):
 command=['/usr/bin/git','-C',str(upstream),*args]
 result=subprocess.run(command,capture_output=True,input=input_bytes,timeout=max(.01,min(10,24-(time.monotonic()-started))))
 row={'command':command,'returncode':result.returncode,'stdout_sha256':sha(result.stdout),'stderr_sha256':sha(result.stderr),
      'stdout_bytes':len(result.stdout),'stderr_bytes':len(result.stderr)}
 if input_bytes is not None:row.update(stdin_sha256=sha(input_bytes),stdin_bytes=len(input_bytes))
 rows.append(row)
 (stage/'commands.json').write_text(json.dumps(rows,indent=2)+chr(10))
 if len(result.stdout)+len(result.stderr)>1024**2:raise ValueError('Git output byte cap')
 return result
def required(*args):
 result=git(*args)
 if result.returncode:raise RuntimeError('Git command failed; cached-only, no network fallback')
 return result.stdout
# Inspect local/worktree config names without following includes before source/status operations.
for scope in ('--local','--worktree'):
 keys=required('config',scope,'--no-includes','--name-only','--list').decode().lower().splitlines()
 if any(k.startswith(('include','filter.','url.','credential.','http.','https.','diff.','merge.','core.sshcommand','core.gitproxy')) for k in keys):
  raise ValueError('unreviewed repository config routing/filter/auth')
sys.path.insert(0,str(root/'src'))
from knowledge_tracing.akt.provenance import verify_upstream
identity=verify_upstream(upstream,profile['pin'])
expected={'commit':profile['pin'],'tree':profile['tree'],'remote':profile['url'],'files':profile['lf']}
if identity!=expected:raise ValueError('actual Git identity/3LF mismatch')
if required('status','--porcelain','--untracked-files=all').strip():raise ValueError('dirty checkout')
if {p.name for p in upstream.iterdir() if p.name!='.git'}!=set(profile['lf']):raise ValueError('worktree must contain original3only')
if set(required('sparse-checkout','list').decode().splitlines())!={'/akt.py','/README.md','/LICENSE'}:
 raise ValueError('unexpected original sparse patterns; no rewrite')
raw=helper['read_regular'](stage/'input/load_data.py')
local_profile=helper['read_regular'](stage/'input/upstream-loader-profile01.json')
if sha(local_profile)!=profile['local_profile_sha']:raise ValueError('local-derived profile bytes mismatch')
meta=json.loads(local_profile)
if meta['commit']!=profile['pin'] or meta['path']!='load_data.py' or meta['git_blob_id']!=profile['loader_blob'] or meta['sha256']!=profile['loader_sha'] or meta['bytes']!=6428:
 raise ValueError('local-derived profile identity mismatch')
oid=required('rev-parse',profile['pin']+':load_data.py').decode().strip()
actual=hashlib.sha1(b'blob '+str(len(raw)).encode()+bytes([0])+raw).hexdigest()
if len(raw)!=6428 or sha(raw)!=profile['loader_sha'] or oid!=profile['loader_blob'] or actual!=oid:
 raise ValueError('transferred loader size/SHA/blob mismatch BEFORE Git object write')
ast.parse(raw) # Syntax only, not source/model execution.
written=git('hash-object','-w','--stdin',input_bytes=raw)
if written.returncode or written.stdout.decode().strip()!=profile['loader_blob']:raise ValueError('actual Git object cache write mismatch')
if required('cat-file','blob','HEAD:load_data.py')!=raw:raise ValueError('actual HEAD loader blob differs from transferred bytes')
required('sparse-checkout','set','--no-cone','/akt.py','/README.md','/LICENSE','/load_data.py')
after=helper['read_regular'](upstream/'load_data.py')
if after!=raw or sha(after)!=profile['loader_sha']:raise ValueError('materialized loader mismatch')
if any(helper['read_regular'](upstream/n)!=data for n,data in before.items()):raise ValueError('original3source bytes changed')
if verify_upstream(upstream,profile['pin'])!=identity or required('status','--porcelain','--untracked-files=all').strip():raise ValueError('source Git identity/cleanliness drift')
if {p.name for p in upstream.iterdir() if p.name!='.git'}!=set(profile['lf'])|{'load_data.py'}:raise ValueError('unexpected sparse worktree output')
if helper['verify_kit']()!=kit_sha:raise ValueError('kit source drift')
print(json.dumps({'status':'MATERIALIZED_TRANSFERRED_PINNED_LOADER_SOURCE_ONLY','mutation_attempted':True,'commands':rows,
 'source_origin':'LOCAL_PINNED_GIT_BLOB_TRANSFER','local_loader_profile_sha256':profile['local_profile_sha'],
 'source_before_after':identity,'loader':{'path':'load_data.py','sha256':sha(after),'git_blob_id':oid,'bytes':len(after)},
 'kit_receipt_sha256':kit_sha,'git_transport_allowed':False,'model_or_optimizer_steps':0,'gate_reruns':0}))
'''

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--expected-source-sha256',required=True);parser.add_argument('--approval-reference',required=True)
    args=parser.parse_args();validate_pin_inventory({'operation_source':args.expected_source_sha256});start=time.monotonic();wall=time.time()
    if not (os.name=='posix' and platform.system()=='Linux' and sys.executable=='/usr/bin/python3' and sys.prefix=='/usr'
            and ROOT.is_dir() and ROOT.resolve()==ROOT and ROOT.stat().st_uid==os.getuid()
            and not STAGE.exists() and not STAGE.is_symlink()):raise ValueError('owned fresh Linux stage required')
    STAGE.mkdir(exist_ok=False);result={'status':'FAILED_TRANSFERRED_LOADER_RETAIN_PARTIAL','children':0,'git_transport_allowed':False,'source_origin':'LOCAL_PINNED_GIT_BLOB_TRANSFER','local_loader_profile_sha256':LOCAL_LOADER_PROFILE_SHA,
                                     'optimizer_steps':0,'model_steps':0,'gate_reruns':0,'approval_reference':args.approval_reference}
    process=None;helper=None;cleanup={'attempted':False,'accepted':False,'events':[]};peak=0
    def check():
        nonlocal peak
        if not all(math.isfinite(v) and 0<=v<=30 for v in (time.monotonic()-start,time.time()-wall)):raise TimeoutError('overall30s')
        if (STAGE/'CANCEL').exists():raise RuntimeError('cancelled')
        size=0
        for base in (STAGE,UPSTREAM):
            for parent,_,names in os.walk(base,followlinks=False):
                for name in names:
                    try:size+=os.lstat(Path(parent)/name).st_size
                    except FileNotFoundError:continue
        peak=max(peak,size)
        if size>128*1024**2 or shutil.disk_usage(ROOT).free<30*1024**3:raise OSError('cooperative source/storage cap')
    try:
        source=Path(__file__).absolute()
        if source!=ROOT/'materialize_upstream_loader04.py' or sha(source.read_bytes())!=args.expected_source_sha256 or not args.approval_reference.strip():
            raise ValueError('reviewed exact source and reference required')
        if os.environ.get('COLAB_GPU') not in (None,'','0') or os.environ.get('COLAB_TPU_ADDR') or list(Path('/dev').glob('nvidia[0-9]*')):raise ValueError('CPU host only')
        # Preserve existing checkout source, prior failed checkout/Gate and accepted LF audit bytes.
        for name,digest in PINS.items():
            path=ROOT/name
            if path.is_symlink() or sha(path.read_bytes())!=digest:raise ValueError('preserved input pin mismatch')
        helper=runpy.run_path(str(ROOT/'upstream_checkout01.py'));helper['verify_kit']()
        for parent in (UPSTREAM,*UPSTREAM.parents):
            if parent.is_symlink():raise ValueError('upstream ancestor symlink')
            if parent==ROOT:break
        if (UPSTREAM/'load_data.py').exists() or (UPSTREAM/'load_data.py').is_symlink():raise FileExistsError('loader already present; no overwrite/retry')
        raw=base64.b64decode(LOADER_BASE64,validate=True);local_profile=base64.b64decode(PROFILE_BASE64,validate=True)
        validate_loader(raw,LOADER_BLOB)
        if sha(local_profile)!=LOCAL_LOADER_PROFILE_SHA:raise ValueError('transported profile SHA mismatch')
        inputs=STAGE/'input';inputs.mkdir(exist_ok=False)
        copies=[]
        for name,payload in (('load_data.py',raw),('upstream-loader-profile01.json',local_profile)):
            path=inputs/name
            with path.open('xb') as stream:stream.write(payload)
            after=helper['read_regular'](path)
            if after!=payload:raise ValueError('transport payload copy drift')
            copies.append({'path':'input/'+name,'bytes':len(payload),'sha256_before_copy':sha(payload),'sha256_after_copy':sha(after)})
        with (STAGE/'input-copy.json').open('x',encoding='utf-8') as stream:json.dump({'source_origin':'LOCAL_PINNED_GIT_BLOB_TRANSFER','copies':copies},stream,indent=2);stream.write(chr(10))
        (STAGE/'home').mkdir();env=isolated_environment(os.environ)
        profile={'pin':PIN,'tree':TREE,'url':URL,'lf':LF,'loader_sha':LOADER_SHA,'loader_blob':LOADER_BLOB,'local_profile_sha':LOCAL_LOADER_PROFILE_SHA}
        script=STAGE/'loader-child.py'
        with script.open('x',encoding='utf-8') as stream:stream.write(CHILD.replace('PROFILE_CONSTANTS',repr(profile)))
        check()
        with (STAGE/'child.stdout').open('xb') as stdout,(STAGE/'child.stderr').open('xb') as stderr:
            process=subprocess.Popen([str(ROOT/'.venv/bin/python'),'-I','-B',str(script)],cwd=ROOT,env=env,stdout=stdout,stderr=stderr,start_new_session=True)
            result['children']=1
            try:
                while process.poll() is None:
                    check()
                    if time.monotonic()-start>25:raise TimeoutError('reserve cleanup within30s')
                    try:process.wait(timeout=.1)
                    except subprocess.TimeoutExpired:pass
            finally:helper['cleanup_once'](process,cleanup)
        if process.returncode!=0 or cleanup['accepted'] is not True:raise RuntimeError('child/cleanup failed')
        payload=json.loads(helper['read_regular'](STAGE/'child.stdout'))
        if payload['status']!='MATERIALIZED_TRANSFERRED_PINNED_LOADER_SOURCE_ONLY':raise ValueError('unexpected outcome')
        for name,digest in PINS.items():
            if sha(helper['read_regular'](ROOT/name))!=digest:raise ValueError('historical source/evidence changed')
        if sha(source.read_bytes())!=args.expected_source_sha256:raise ValueError('operation source drift')
        if any(sha(helper['read_regular'](UPSTREAM/n))!=digest for n,digest in LF.items()):raise ValueError('original3LF changed')
        if sha(helper['read_regular'](STAGE/'input/load_data.py'))!=LOADER_SHA or sha(helper['read_regular'](STAGE/'input/upstream-loader-profile01.json'))!=LOCAL_LOADER_PROFILE_SHA:raise ValueError('copied input drift')
        result.update(status=payload['status'],audit=payload,source_sha256=args.expected_source_sha256,preserved_input_sha256=PINS,source_origin='LOCAL_PINNED_GIT_BLOB_TRANSFER',input_copy=copies);check()
    except Exception as exc:
        result.update(status='FAILED_TRANSFERRED_LOADER_RETAIN_PARTIAL',error_type=type(exc).__name__,error=str(exc))
        with (STAGE/'failure.log').open('x',encoding='utf-8') as stream:stream.write(traceback.format_exc())
    finally:
        if helper is not None:helper['cleanup_once'](process,cleanup)
        result.update(cleanup=cleanup,elapsed_seconds=time.monotonic()-start,elapsed_wall_seconds=time.time()-wall,
                      timeout_seconds=30,peak_observed_source_bytes=peak,storage_monitor_cooperative=True)
        if not all(math.isfinite(v) and 0<=v<=30 for v in (result['elapsed_seconds'],result['elapsed_wall_seconds'])):
            result['status']='REJECTED_RESOURCE_BOUND_RETAIN_PARTIAL'
        with (STAGE/'result.json').open('x',encoding='utf-8') as stream:json.dump(result,stream,indent=2,allow_nan=False);stream.write('\n')
        inventory={p.relative_to(STAGE).as_posix():{'sha256':sha(p.read_bytes()),'bytes':p.stat().st_size} for p in STAGE.iterdir() if p.is_file()}
        if (STAGE/'input').is_dir():
            for p in (STAGE/'input').iterdir():
                if p.is_file():inventory[p.relative_to(STAGE).as_posix()]={'sha256':sha(p.read_bytes()),'bytes':p.stat().st_size}
        with (STAGE/'output-manifest.json').open('x',encoding='utf-8') as stream:json.dump({'status':result['status'],'outputs':inventory},stream,indent=2);stream.write('\n')
        print(json.dumps({'status':result['status'],'elapsed_seconds':result['elapsed_seconds'],
                          'result_sha256':sha((STAGE/'result.json').read_bytes()),'output_manifest_sha256':sha((STAGE/'output-manifest.json').read_bytes())}))
    return 0 if result['status']=='MATERIALIZED_TRANSFERRED_PINNED_LOADER_SOURCE_ONLY' else 1
if __name__=='__main__':raise SystemExit(main())
