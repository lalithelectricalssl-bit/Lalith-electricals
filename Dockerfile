FROM frappe/erpnext:v16.53.0@sha256:b961d69ed3265f44f712f40be58a3e6a22c8662f61a7e1a8097765534e3e9be2
USER frappe
COPY --chown=frappe:0 apps/lalith_shop /home/frappe/frappe-bench/apps/lalith_shop
COPY --chown=frappe:0 deploy/runtime.py /home/frappe/lalith_runtime.py
RUN /home/frappe/frappe-bench/env/bin/pip install --no-deps -e /home/frappe/frappe-bench/apps/lalith_shop
