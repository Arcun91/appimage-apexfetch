# ==============================================================================
# ApexFetch Makefile
# ==============================================================================

PREFIX ?= /usr/local
BINDIR ?= $(PREFIX)/bin

.PHONY: all run json test appimage install uninstall clean help

all: help

help:
	@echo "ApexFetch Build & Run Targets:"
	@echo "  make run        - Execute ApexFetch locally"
	@echo "  make json       - Output system telemetry in JSON format"
	@echo "  make appimage   - Package into standalone Linux AppImage"
	@echo "  make install    - Install apexfetch binary to $(BINDIR)"
	@echo "  make uninstall  - Remove apexfetch binary from $(BINDIR)"
	@echo "  make clean      - Clean build artifacts"

run:
	./apexfetch.py

json:
	./apexfetch.py --json

test:
	python3 -m py_compile apexfetch.py
	./apexfetch.py --no-logo
	./apexfetch.py --json > /dev/null

appimage:
	./build_appimage.sh

install:
	install -d $(DESTDIR)$(BINDIR)
	install -m 755 apexfetch.py $(DESTDIR)$(BINDIR)/apexfetch
	install -d $(DESTDIR)$(PREFIX)/share/applications
	install -m 644 apexfetch.desktop $(DESTDIR)$(PREFIX)/share/applications/apexfetch.desktop
	install -d $(DESTDIR)$(PREFIX)/share/icons/hicolor/scalable/apps
	install -m 644 apexfetch.svg $(DESTDIR)$(PREFIX)/share/icons/hicolor/scalable/apps/apexfetch.svg

uninstall:
	rm -f $(DESTDIR)$(BINDIR)/apexfetch
	rm -f $(DESTDIR)$(PREFIX)/share/applications/apexfetch.desktop
	rm -f $(DESTDIR)$(PREFIX)/share/icons/hicolor/scalable/apps/apexfetch.svg

clean:
	rm -rf build dist __pycache__ *.spec
