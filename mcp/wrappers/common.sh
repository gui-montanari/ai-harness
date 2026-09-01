#!/bin/bash

choose_launch_mode() {
  local client_name="$1"
  echo
  echo "Como deseja iniciar o $client_name?"
  echo "  1. Normal (nova sessão)"
  echo "  2. Normal + continuar sessão"
  echo "  3. New YOLO / auto-approve (nova sessão)"
  echo "  4. YOLO / auto-approve + continuar sessão"
  echo "  [q] Não iniciar"
  read -r -p "Escolha: " launch_mode
  case "$launch_mode" in
    1|2|3|4) return 0 ;;
    q|Q) echo "Saindo sem iniciar o $client_name."; return 1 ;;
    *) echo "Opção inválida. Iniciando no modo Normal."; launch_mode=1 ;;
  esac
}

choose_resume_target() {
  while true; do
    echo
    echo "Qual sessão deseja continuar?"
    echo "  1. Última sessão"
    echo "  2. Sessão específica por ID"
    echo "  [q] Cancelar"
    read -r -p "Escolha: " resume_choice
    case "$resume_choice" in
      1) resume_kind="last"; session_id=""; return 0 ;;
      2)
        while true; do
          read -r -p "Digite o ID da sessão: " session_id
          if [ -z "$session_id" ]; then
            echo "O ID não pode ficar vazio."
            continue
          fi
          echo "Sessão informada: $session_id"
          read -r -p "Confirma continuar esta sessão? [s/N]: " confirm
          case "$confirm" in
            s|S|y|Y) resume_kind="specific"; return 0 ;;
            *) echo "Sessão não confirmada. Informe novamente ou use Ctrl+C para sair." ;;
          esac
        done
        ;;
      q|Q) return 1 ;;
      *) echo "Opção inválida." ;;
    esac
  done
}
