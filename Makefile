# ===========================================================================
# secure-web-lab — Clase 01 por fases
#
# Este Makefile es solo un atajo: toda la lógica está en ./lab.sh, para que
# Linux/macOS/WSL y Windows (lab.ps1) hagan exactamente lo mismo.
#
#   make setup / fase1-red / fase2-build / fase3-web
#   make test-fase3 / test-clase02 / test-todo
#   make fase4-ataque / credenciales (la fase 4 es una demo, no tiene tests)
#   make demo-pasivo / demo-activo / estado / down / limpiar
#
# Windows PowerShell (sin make):   .\lab.ps1 <mismo-comando>
# ===========================================================================
LAB = ./lab.sh

.PHONY: ayuda entorno setup fase1-red fase1-plan fase2-build fase3-web test-fase3 fase4-ataque \
        test-clase02 test-clase03 test-clase04 test-todo test-fase4 credenciales demo-pasivo demo-activo estado down limpiar \
        up test test-clase01 logs rebuild

ayuda:         ; @$(LAB) ayuda
entorno:       ; @$(LAB) entorno
setup:         ; @$(LAB) setup
fase1-red:     ; @$(LAB) fase1-red
fase1-plan:    ; @$(LAB) fase1-plan
fase2-build:   ; @$(LAB) fase2-build
fase3-web:     ; @$(LAB) fase3-web
test-fase3:    ; @$(LAB) test-fase3
test-clase02:  ; @$(LAB) test-clase02
test-clase03:  ; @$(LAB) test-clase03
test-clase04:  ; @$(LAB) test-clase04
test-todo:     ; @$(LAB) test-todo
fase4-ataque:  ; @$(LAB) fase4-ataque
test-fase4:    ; @$(LAB) test-fase4
credenciales:  ; @$(LAB) credenciales
demo-pasivo:   ; @$(LAB) demo-pasivo
demo-activo:   ; @$(LAB) demo-activo
estado:        ; @$(LAB) estado
down:          ; @$(LAB) down
limpiar:       ; @$(LAB) limpiar

# --- Alias de compatibilidad (guiones anteriores) --------------------------
up: fase3-web
test-clase01: test-fase3

logs:
	COMPOSE_PROFILES=ataque docker compose logs -f --tail=100

test: test-todo

rebuild:
	@$(LAB) down
	docker compose build --no-cache
	@$(LAB) fase3-web
