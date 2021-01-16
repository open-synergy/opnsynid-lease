# Copyright 2019 OpenSynergy Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models


class LeaseOperatingOut(models.Model):
    _name = "lease.operating_out"
    _description = "Operating Lease Out"
    _inherit = [
        "lease.operating_common",
    ]

    @api.depends(
        "type_id",
    )
    @api.multi
    def _compute_policy(self):
        _super = super(LeaseOperatingOut, self)
        _super._compute_policy()

    period_ids = fields.One2many(
        comodel_name="lease.operating_schedule_out",
        inverse_name="lease_id",
    )
    tax_ids = fields.Many2many(
        string="Taxes",
        comodel_name="account.tax",
        relation="rel_lease_operating_out_2_tax",
        column1="lease_id",
        column2="tax_id",
    )


class LeaseOperatingScheduleOut(models.Model):
    _name = "lease.operating_schedule_out"
    _inherit = ["lease.operating_schedule_common"]
    _description = "Operating Lease Out Lease Period"

    lease_id = fields.Many2one(
        comodel_name="lease.operating_out",
        ondelete="cascade",
    )
    lease_state = fields.Selection(
        related="lease_id.state",
        store=True,
    )
