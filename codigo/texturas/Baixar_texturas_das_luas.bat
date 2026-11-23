@echo off
chcp 65001 >nul
title Baixar texturas das luas (NASA/JPL)
cd /d "%~dp0"
echo Baixando 18 texturas de luas do site da NASA (science.nasa.gov)...
echo.
if exist "lua_io.jpg" (echo  ja tem: lua_io.jpg) else (curl.exe -L -f -s -S -o "lua_io.jpg" "https://assets.science.nasa.gov/content/dam/science/cds/3d/resources/image/jupiter---io-(b)/Jupiter%%20-%%20Io%%20(B).jpg" && echo  ok: lua_io.jpg || echo  FALHOU: lua_io.jpg)
if exist "lua_europa.jpg" (echo  ja tem: lua_europa.jpg) else (curl.exe -L -f -s -S -o "lua_europa.jpg" "https://assets.science.nasa.gov/content/dam/science/cds/3d/resources/image/jupiter---europa/Jupiter%%20-%%20Europa.jpg" && echo  ok: lua_europa.jpg || echo  FALHOU: lua_europa.jpg)
if exist "lua_ganimedes.jpg" (echo  ja tem: lua_ganimedes.jpg) else (curl.exe -L -f -s -S -o "lua_ganimedes.jpg" "https://assets.science.nasa.gov/content/dam/science/cds/3d/resources/image/jupiter---ganymede/Jupiter%%20-%%20Ganymede.jpg" && echo  ok: lua_ganimedes.jpg || echo  FALHOU: lua_ganimedes.jpg)
if exist "lua_calisto.jpg" (echo  ja tem: lua_calisto.jpg) else (curl.exe -L -f -s -S -o "lua_calisto.jpg" "https://assets.science.nasa.gov/content/dam/science/cds/3d/resources/image/jupiter---callisto/Jupiter%%20-%%20Callisto.jpg" && echo  ok: lua_calisto.jpg || echo  FALHOU: lua_calisto.jpg)
if exist "lua_mimas.jpg" (echo  ja tem: lua_mimas.jpg) else (curl.exe -L -f -s -S -o "lua_mimas.jpg" "https://assets.science.nasa.gov/content/dam/science/cds/3d/resources/image/saturn---mimas/Saturn%%20-%%20Mimas.jpg" && echo  ok: lua_mimas.jpg || echo  FALHOU: lua_mimas.jpg)
if exist "lua_encelado.jpg" (echo  ja tem: lua_encelado.jpg) else (curl.exe -L -f -s -S -o "lua_encelado.jpg" "https://assets.science.nasa.gov/content/dam/science/cds/3d/resources/image/saturn---enceladus/Saturn%%20-%%20Enceladus.jpg" && echo  ok: lua_encelado.jpg || echo  FALHOU: lua_encelado.jpg)
if exist "lua_tetis.jpg" (echo  ja tem: lua_tetis.jpg) else (curl.exe -L -f -s -S -o "lua_tetis.jpg" "https://assets.science.nasa.gov/content/dam/science/cds/3d/resources/image/saturn---tethys/Saturn%%20-%%20Tethys.jpg" && echo  ok: lua_tetis.jpg || echo  FALHOU: lua_tetis.jpg)
if exist "lua_dione.jpg" (echo  ja tem: lua_dione.jpg) else (curl.exe -L -f -s -S -o "lua_dione.jpg" "https://assets.science.nasa.gov/content/dam/science/cds/3d/resources/image/saturn---dione/Saturn%%20-%%20Dione.jpg" && echo  ok: lua_dione.jpg || echo  FALHOU: lua_dione.jpg)
if exist "lua_reia.jpg" (echo  ja tem: lua_reia.jpg) else (curl.exe -L -f -s -S -o "lua_reia.jpg" "https://assets.science.nasa.gov/content/dam/science/cds/3d/resources/image/saturn---rhea/Saturn%%20-%%20Rhea.jpg" && echo  ok: lua_reia.jpg || echo  FALHOU: lua_reia.jpg)
if exist "lua_japeto.jpg" (echo  ja tem: lua_japeto.jpg) else (curl.exe -L -f -s -S -o "lua_japeto.jpg" "https://assets.science.nasa.gov/content/dam/science/cds/3d/resources/image/saturn---iapetus/Saturn%%20-%%20Iapetus.jpg" && echo  ok: lua_japeto.jpg || echo  FALHOU: lua_japeto.jpg)
if exist "lua_miranda.jpg" (echo  ja tem: lua_miranda.jpg) else (curl.exe -L -f -s -S -o "lua_miranda.jpg" "https://assets.science.nasa.gov/content/dam/science/cds/3d/resources/image/uranus---miranda/Uranus%%20-%%20Miranda.jpg" && echo  ok: lua_miranda.jpg || echo  FALHOU: lua_miranda.jpg)
if exist "lua_ariel.jpg" (echo  ja tem: lua_ariel.jpg) else (curl.exe -L -f -s -S -o "lua_ariel.jpg" "https://assets.science.nasa.gov/content/dam/science/cds/3d/resources/image/uranus---ariel/Uranus%%20-%%20Ariel.jpg" && echo  ok: lua_ariel.jpg || echo  FALHOU: lua_ariel.jpg)
if exist "lua_umbriel.jpg" (echo  ja tem: lua_umbriel.jpg) else (curl.exe -L -f -s -S -o "lua_umbriel.jpg" "https://assets.science.nasa.gov/content/dam/science/cds/3d/resources/image/uranus---umbriel/Uranus%%20-%%20Umbriel.jpg" && echo  ok: lua_umbriel.jpg || echo  FALHOU: lua_umbriel.jpg)
if exist "lua_titania.jpg" (echo  ja tem: lua_titania.jpg) else (curl.exe -L -f -s -S -o "lua_titania.jpg" "https://assets.science.nasa.gov/content/dam/science/cds/3d/resources/image/uranus---titania/Uranus%%20-%%20Titania.jpg" && echo  ok: lua_titania.jpg || echo  FALHOU: lua_titania.jpg)
if exist "lua_oberon.jpg" (echo  ja tem: lua_oberon.jpg) else (curl.exe -L -f -s -S -o "lua_oberon.jpg" "https://assets.science.nasa.gov/content/dam/science/cds/3d/resources/image/uranus---oberon/Uranus%%20-%%20Oberon.jpg" && echo  ok: lua_oberon.jpg || echo  FALHOU: lua_oberon.jpg)
if exist "lua_tritao.jpg" (echo  ja tem: lua_tritao.jpg) else (curl.exe -L -f -s -S -o "lua_tritao.jpg" "https://assets.science.nasa.gov/content/dam/science/cds/3d/resources/image/neptune---triton/Neptune%%20-%%20Triton.jpg" && echo  ok: lua_tritao.jpg || echo  FALHOU: lua_tritao.jpg)
if exist "lua_fobos.jpg" (echo  ja tem: lua_fobos.jpg) else (curl.exe -L -f -s -S -o "lua_fobos.jpg" "https://assets.science.nasa.gov/content/dam/science/cds/3d/resources/image/mars---phobos/Mars%%20-%%20Phobos.jpg" && echo  ok: lua_fobos.jpg || echo  FALHOU: lua_fobos.jpg)
if exist "lua_deimos.jpg" (echo  ja tem: lua_deimos.jpg) else (curl.exe -L -f -s -S -o "lua_deimos.jpg" "https://assets.science.nasa.gov/content/dam/science/cds/3d/resources/image/mars---deimos/Mars%%20-%%20Deimos.jpg" && echo  ok: lua_deimos.jpg || echo  FALHOU: lua_deimos.jpg)
echo.
echo Pronto. Agora rode o simulador de novo (Rodar_simulador.bat na pasta codigo).
echo Se alguma deu FALHOU, confira a internet e rode de novo.
pause
