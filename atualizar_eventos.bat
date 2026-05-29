@echo off
cd /d "C:\Users\b.souza\OneDrive - Alvarez and Marsal\PMO de Performance\Report_GitHub"
echo =====================================
echo Atualizando Dashboard Eventos...
echo =====================================
echo Gerando novo index.html...
python gerar_eventos.py
echo Salvando alteracoes...
git add .
git commit -m "Atualizacao automatica dashboard eventos"
echo Sincronizando com GitHub...
git pull --rebase origin main
echo Enviando atualizacoes...
git push origin main
echo.
echo =====================================
echo Dashboard atualizado!
echo Aguarde 1-3 minutos.
echo =====================================
pause