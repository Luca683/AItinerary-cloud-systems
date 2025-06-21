#!/bin/sh

# Avvia il server Ollama in background (default ascolta porta 11434)
ollama serve &

# Attendi che il server sia pronto (puoi aumentare il tempo se serve)
sleep 30

# Se modello non è presente, scaricalo
if ! ollama list | grep -q gemma3:1b; then
  echo "Scarico modello gemma3:1b.."
  ollama pull gemma3:1b
fi

# Mantieni il processo in foreground per tenere il container vivo
wait