@echo off
cd /d "C:\Users\b.souza\Alvarez and Marsal\[GERDAU] Implantação de PMO - Reports GERDAU\PMO de Performance\Report_GitHub"
echo =====================================
echo Atualizando Dashboard Eventos...
echo =====================================
echo Gerando novo index.html...
python gerar_eventos.py
echo Sincronizando com GitHub...
git pull origin main
echo Enviando atualizacoes...
git add .
git commit -m "Atualizacao automatica dashboard eventos"
git push origin main
echo.
echo =====================================
echo Dashboard atualizado!
echo Aguarde 1-3 minutos.
echo =====================================
pause
