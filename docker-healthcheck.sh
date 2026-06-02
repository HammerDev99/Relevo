#!/bin/bash
# Healthcheck modo-consciente: API→:8000, GUI→:8501
if [ "${RELEVO_MODE:-api}" = "gui" ]; then
    curl -f http://localhost:8501/_stcore/health
else
    curl -f http://localhost:8000/
fi
