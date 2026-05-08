"""
Agent Start Endpoint Update — Phase 7
Wires POST /agent/start to the full orchestrator.
"""
from pydantic import BaseModel
from typing import Optional
from fastapi import BackgroundTasks

# Append to existing agent.py — handled by updating the router registration in main.py
# This file adds the /agent/start route

class StartRequest(BaseModel):
    role:        Optional[str]  = None
    location:    Optional[str]  = None
    remote:      bool           = False
    skip_hunt:   bool           = False
    skip_apply:  bool           = False
