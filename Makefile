SHELL := /bin/bash

.PHONY: help check list

help:
	@echo "Redmi 9A kernel 7.1 mainline"
	@echo ""
	@echo "  make check   bash -n 检查 scripts/、ubuntu/、gpu/ 下所有 shell 脚本"
	@echo "  make list    统计各目录文件数与体积"
	@echo ""

check:
	@fail=0; \
	while IFS= read -r -d '' f; do \
		if ! bash -n "$$f" 2>/dev/null; then echo "SYNTAX FAIL: $$f"; fail=1; fi; \
	done < <(find scripts ubuntu -name '*.sh' -print0); \
	if [ $$fail -eq 0 ]; then echo "check: OK"; else exit 1; fi

list:
	@for d in docs configs scripts src data dist logs archive ubuntu; do \
		if [ -d "$$d" ]; then \
			printf '%-10s %5s files  %8s\n' "$$d" "$$(find "$$d" -type f | wc -l)" "$$(du -sh "$$d" | cut -f1)"; \
		fi; \
	done
