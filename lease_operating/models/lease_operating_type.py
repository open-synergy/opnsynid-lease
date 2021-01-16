# Copyright 2019 OpenSynergy Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models


class LeaseOperatingType(models.Model):
    _name = "lease.operating_type"
    _description = "Operating Lease Type"

    @api.model
    def _default_currency_id(self):
        return self.env.user.company_id.currency_id.id

    name = fields.Char(
        string="Operating Lease Type",
        required=True,
    )
    code = fields.Char(
        string="Code",
        required=True,
    )
    active = fields.Boolean(
        string="Active",
        default=True,
    )
    note = fields.Text(
        string="Note",
    )
    decription = fields.Text(
        string="Description",
    )
    lease_sequence_id = fields.Many2one(
        string="Lease Sequence",
        comodel_name="ir.sequence",
        company_dependent=True,
    )
    direction = fields.Selection(
        string="Direction",
        selection=[
            ("in", "In"),
            ("out", "Out"),
        ],
        required=True,
    )
    currency_id = fields.Many2one(
        string="Currency",
        comodel_name="res.currency",
        required=True,
        default=lambda self: self._default_currency_id(),
    )
    maximum_lease_amount = fields.Float(
        string="Maximum Lease Amount",
        required=True,
        company_dependent=True,
    )
    maximum_lease_installment_period = fields.Integer(
        string="Maximum Installment Period",
        company_dependent=True,
    )
    lease_period_lenght = fields.Selection(
        string="Period Lenght",
        selection=[
            ("month", "Monthly"),
            ("year", "Yearly"),
        ],
        required=True,
    )
    lease_payment_time = fields.Selection(
        string="Lease Payment Time",
        selection=[
            ("advance", "Advance"),
            ("arrear", "Arrear"),
        ],
        required=True,
        default="arrear",
    )
    lease_confirm_grp_ids = fields.Many2many(
        string="Allow To Confirm Lease",
        comodel_name="res.groups",
        relation="rel_lease_type_confirm_lease",
        column1="type_id",
        column2="group_id",
    )
    lease_start_grp_ids = fields.Many2many(
        string="Allow To Start Lease",
        comodel_name="res.groups",
        relation="rel_lease_type_start_lease",
        column1="type_id",
        column2="group_id",
    )
    lease_finish_grp_ids = fields.Many2many(
        string="Allow To Finish Lease",
        comodel_name="res.groups",
        relation="rel_lease_type_finish_lease",
        column1="type_id",
        column2="group_id",
    )
    lease_cancel_grp_ids = fields.Many2many(
        string="Allow To Cancel Lease",
        comodel_name="res.groups",
        relation="rel_lease_type_cancel_lease",
        column1="type_id",
        column2="group_id",
    )
    lease_restart_grp_ids = fields.Many2many(
        string="Allow To Restart Lease",
        comodel_name="res.groups",
        relation="rel_lease_type_restart_lease",
        column1="type_id",
        column2="group_id",
    )
    lease_restart_approval_grp_ids = fields.Many2many(
        string="Allow To Restart Lease Approval",
        comodel_name="res.groups",
        relation="rel_lease_type_restart_lease_approval",
        column1="type_id",
        column2="group_id",
    )
