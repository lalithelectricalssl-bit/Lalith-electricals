# Upstream software and licences

- [ERPNext v16.53.0](https://github.com/frappe/erpnext/releases/tag/v16.53.0) supplies the ERP system. The Dockerfile pins its official multi-architecture image by digest, including linux/arm64 for the Mac M2 and linux/amd64 for the Linux check.
- The service layout comes from [Frappe Docker](https://github.com/frappe/frappe_docker/tree/fbf76edcf5791b1d9743955b85caf0a19974d5a6), with its [MIT licence](../deploy/Frappe-Docker-LICENSE). The application only publishes the localhost web port.
- MariaDB 11.8 and Redis 8.6 use pinned official images. The custom app is Lalith Shop 0.1.0 under GPL-3.0-or-later.
- The backup and recovery commands use Frappe Bench [backup](https://docs.frappe.io/framework/user/en/bench/reference/backup) and [restore](https://docs.frappe.io/framework/user/en/bench/reference/restore).
