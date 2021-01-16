# Copyright 2019 OpenSynergy Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from dateutil import relativedelta
from openerp import _, api, fields, models
from openerp.exceptions import Warning as UserError


class LeaseOperatingCommon(models.Model):
    _name = "lease.operating_common"
    _description = "Abstract Model for Operating Lease"
    _inherit = [
        "mail.thread",
        "tier.validation",
        "base.sequence_document",
        "base.workflow_policy_object",
        "base.cancel.reason_common",
        "base.terminate.reason_common",
        "custom.info.mixin",
    ]
    _state_from = ["draft", "confirm"]
    _state_to = ["approve"]

    @api.model
    def _default_company_id(self):
        return self.env.user.company_id.id

    @api.model
    def _default_user_id(self):
        return self.env.user.id

    @api.multi
    def _compute_policy(self):
        _super = super(LeaseOperatingCommon, self)
        _super._compute_policy()

    @api.depends(
        "date_start",
        "period_num",
        "lease_period_lenght",
    )
    @api.multi
    def _compute_date_end(self):
        for document in self:
            date_end = False
            if (
                document.date_start
                and document.period_num
                and document.lease_period_lenght
            ):
                dt_date_start = fields.Date.from_string(document.date_start)
                if document.lease_period_lenght == "year":
                    dt_date_end = dt_date_start + relativedelta.relativedelta(
                        years=document.period_num, days=-1
                    )
                else:
                    dt_date_end = dt_date_start + relativedelta.relativedelta(
                        months=document.period_num, days=-1
                    )
                date_end = fields.Date.to_string(dt_date_end)
            document.date_end = date_end

    name = fields.Char(
        string="# Document",
        default="/",
        required=True,
        copy=False,
        readonly=True,
        states={
            "draft": [
                ("readonly", False),
            ],
        },
    )
    company_id = fields.Many2one(
        string="Company",
        comodel_name="res.company",
        required=True,
        default=lambda self: self._default_company_id(),
    )
    partner_id = fields.Many2one(
        string="Partner",
        comodel_name="res.partner",
        required=True,
        readonly=True,
        states={
            "draft": [
                ("readonly", False),
            ],
        },
    )
    currency_id = fields.Many2one(
        string="Currency",
        comodel_name="res.currency",
        related="type_id.currency_id",
        store=True,
    )
    lease_amount = fields.Float(
        string="Lease Amount",
        required=True,
        readonly=True,
        states={
            "draft": [
                ("readonly", False),
            ],
        },
    )
    user_id = fields.Many2one(
        string="Responsible",
        comodel_name="res.users",
        default=lambda self: self._default_user_id(),
        required=True,
        readonly=True,
        states={
            "draft": [
                ("readonly", False),
            ],
        },
    )
    type_id = fields.Many2one(
        string="Type",
        comodel_name="lease.operating_type",
        required=True,
        readonly=True,
        states={
            "draft": [
                ("readonly", False),
            ],
        },
    )
    date_start = fields.Date(
        string="Start Date",
        required=True,
        readonly=True,
        states={
            "draft": [
                ("readonly", False),
            ],
        },
    )
    date_end = fields.Date(
        string="End Date",
        compute="_compute_date_end",
        store=True,
    )
    period_num = fields.Integer(
        string="Period Number",
        required=True,
        readonly=True,
        states={
            "draft": [
                ("readonly", False),
            ],
        },
    )
    lease_period_lenght = fields.Selection(
        string="Period Lenght",
        selection=[
            ("month", "Monthly"),
            ("year", "Yearly"),
        ],
        related="type_id.lease_period_lenght",
        store=True,
        readonly=True,
    )
    analytic_account_id = fields.Many2one(
        string="Analytic Account",
        comodel_name="account.analytic.account",
        readonly=True,
        states={
            "draft": [
                ("readonly", False),
            ],
        },
    )
    period_ids = fields.One2many(
        string="Lease Periods",
        comodel_name="lease.operating_schedule_common",
        inverse_name="lease_id",
        readonly=True,
    )
    accrue_journal_id = fields.Many2one(
        string="Accrue Revenue/Expense Accounting Entry Journal",
        comodel_name="account.journal",
        required=True,
        readonly=True,
        states={
            "draft": [
                ("readonly", False),
            ],
        },
    )
    invoice_journal_id = fields.Many2one(
        string="Invoice Journal",
        comodel_name="account.journal",
        required=True,
        readonly=True,
        states={
            "draft": [
                ("readonly", False),
            ],
        },
    )
    accrue_account_id = fields.Many2one(
        string="Accrue Revenue/Expense Account",
        comodel_name="account.account",
        required=True,
        readonly=True,
        states={
            "draft": [
                ("readonly", False),
            ],
        },
    )
    account_id = fields.Many2one(
        string="Revenue/Expense Account",
        comodel_name="account.account",
        required=True,
        readonly=True,
        states={
            "draft": [
                ("readonly", False),
            ],
        },
    )
    invoice_account_id = fields.Many2one(
        string="AR/AP Account",
        comodel_name="account.account",
        required=True,
        readonly=True,
        states={
            "draft": [
                ("readonly", False),
            ],
        },
    )
    tax_ids = fields.Many2many(
        string="Taxes",
        comodel_name="account.tax",
        readonly=True,
        states={
            "draft": [
                ("readonly", False),
            ],
        },
    )
    note = fields.Text(
        string="Note",
    )
    state = fields.Selection(
        string="State",
        selection=[
            ("draft", "Draft"),
            ("confirm", "Waiting for Approval"),
            ("approve", "Ready to Start"),
            ("open", "In Progress"),
            ("done", "Done"),
            ("terminate", "Terminated"),
            ("cancel", "Cancelled"),
        ],
        copy=False,
        default="draft",
        required=True,
        readonly=True,
    )
    confirm_date = fields.Datetime(
        string="Confirmation Date",
        readonly=True,
        copy=False,
    )
    confirm_user_id = fields.Many2one(
        string="Confirmed By",
        comodel_name="res.users",
        readonly=True,
        copy=False,
    )
    open_date = fields.Datetime(
        string="Start Date",
        readonly=True,
        copy=False,
    )
    open_user_id = fields.Many2one(
        string="Start By",
        comodel_name="res.users",
        readonly=True,
        copy=False,
    )
    done_date = fields.Datetime(
        string="Finish Date",
        readonly=True,
        copy=False,
    )
    done_user_id = fields.Many2one(
        string="Finished By",
        comodel_name="res.users",
        readonly=True,
        copy=False,
    )
    cancel_date = fields.Datetime(
        string="Cancel Date",
        readonly=True,
        copy=False,
    )
    cancel_user_id = fields.Many2one(
        string="Cancelled By",
        comodel_name="res.users",
        readonly=True,
        copy=False,
    )
    terminate_date = fields.Datetime(
        string="Terminate Date",
        readonly=True,
        copy=False,
    )
    terminate_user_id = fields.Many2one(
        string="Terminated By",
        comodel_name="res.users",
        readonly=True,
        copy=False,
    )
    # Policy Field
    confirm_ok = fields.Boolean(
        string="Can Confirm",
        compute="_compute_policy",
    )
    restart_approval_ok = fields.Boolean(
        string="Can Restart Approval",
        compute="_compute_policy",
    )
    open_ok = fields.Boolean(
        string="Can Force Start",
        compute="_compute_policy",
    )
    finish_ok = fields.Boolean(
        string="Can Force Finish",
        compute="_compute_policy",
    )
    cancel_ok = fields.Boolean(
        string="Can Cancel",
        compute="_compute_policy",
    )
    restart_ok = fields.Boolean(
        string="Can Restart",
        compute="_compute_policy",
    )
    terminate_ok = fields.Boolean(
        string="Can Terminate",
        compute="_compute_policy",
    )

    @api.multi
    def action_confirm(self):
        for record in self:
            record.write(record._prepare_confirm_data())
            record.request_validation()

    @api.multi
    def action_approve(self):
        for record in self:
            record.write(record._prepare_approve_data())

    @api.multi
    def action_start(self):
        for record in self:
            record.write(record._prepare_start_data())

    @api.multi
    def action_finish(self):
        for record in self:
            record.write(record._prepare_finish_data())

    @api.multi
    def action_cancel(self):
        for record in self:
            record.write(record._prepare_cancel_data())

    @api.multi
    def action_terminate(self):
        for record in self:
            record.write(record._prepare_terminate_data())

    @api.multi
    def action_restart(self):
        for record in self:
            record.write(record._prepare_restart_data())

    @api.multi
    def action_create_period(self):
        for record in self:
            record.period_ids.unlink()
            record._create_period()

    @api.multi
    def _create_period(self):
        self.ensure_one()
        obj_period = self.env[self._get_period_object_name()]
        dt_period_start = fields.Date.from_string(self.date_start)
        dt_date_end = fields.Date.from_string(self.date_end)
        dt_period_end = False
        total_amount = 0.0
        while not dt_date_end == dt_period_end:
            if self.lease_period_lenght == "year":
                dt_period_end = dt_period_start + relativedelta.relativedelta(
                    day=1, years=1, days=-1
                )
            else:
                dt_period_end = dt_period_start + relativedelta.relativedelta(
                    day=1, months=1, days=-1
                )
            if dt_period_end > dt_date_end:
                dt_period_end = dt_date_end

            period_amount = self._get_period_amount()

            if self.lease_period_lenght == "year":
                if dt_period_start != (
                    dt_period_start + relativedelta.relativedelta(day=1, month=1)
                ):
                    num_days = (
                        dt_period_start + relativedelta.relativedelta(day=1, month=1)
                    ) - dt_period_start
                    period_amount = (period_amount / 365.0) * abs(num_days.days)

            else:
                if dt_period_start != (
                    dt_period_start + relativedelta.relativedelta(day=1)
                ):
                    num_days = (
                        dt_period_start + relativedelta.relativedelta(day=1)
                    ) - dt_period_start
                    period_amount = ((period_amount * 12.0) / 365.0) * abs(
                        num_days.days
                    )

            if dt_period_end == dt_date_end:
                period_amount = self.lease_amount - total_amount

            obj_period.create(
                {
                    "lease_id": self.id,
                    "date_start": fields.Date.to_string(dt_period_start),
                    "date_end": fields.Date.to_string(dt_period_end),
                    "amount": period_amount,
                }
            )
            dt_period_start = dt_period_end + relativedelta.relativedelta(days=1)
            total_amount += period_amount

    @api.multi
    def _get_period_amount(self):
        self.ensure_one()
        return self.lease_amount / self.period_num

    @api.multi
    def _get_period_object_name(self):
        self.ensure_one()
        model_name = str(self._model)
        obj_field = self.env["ir.model.fields"]
        criteria = [
            ("model_id.model", "=", model_name),
            ("name", "=", "period_ids"),
        ]
        field = obj_field.search(criteria)[0]
        return field.relation

    @api.multi
    def _prepare_confirm_data(self):
        self.ensure_one()
        return {
            "state": "confirm",
            "confirm_date": fields.Datetime.now(),
            "confirm_user_id": self.env.user.id,
        }

    @api.multi
    def _prepare_approve_data(self):
        self.ensure_one()
        sequence = self._create_sequence()
        return {
            "state": "approve",
            "name": sequence,
        }

    @api.multi
    def _prepare_start_data(self):
        self.ensure_one()
        return {
            "state": "open",
            "open_date": fields.Datetime.now(),
            "open_user_id": self.env.user.id,
        }

    @api.multi
    def _prepare_finish_data(self):
        self.ensure_one()
        return {
            "state": "done",
            "done_date": fields.Datetime.now(),
            "done_user_id": self.env.user.id,
        }

    @api.multi
    def _prepare_cancel_data(self):
        self.ensure_one()
        return {
            "state": "cancel",
            "cancel_date": fields.Datetime.now(),
            "cancel_user_id": self.env.user.id,
        }

    @api.multi
    def _prepare_terminate_data(self):
        self.ensure_one()
        return {
            "state": "terminate",
            "terminate_date": fields.Datetime.now(),
            "terminate_user_id": self.env.user.id,
        }

    @api.multi
    def _prepare_restart_data(self):
        self.ensure_one()
        return {
            "state": "draft",
            "confirm_date": False,
            "confirm_user_id": False,
            "open_date": False,
            "open_user_id": False,
            "done_date": False,
            "done_user_id": False,
            "cancel_date": False,
            "cancel_user_id": False,
            "terminate_date": False,
            "terminate_user_id": False,
        }

    @api.multi
    def unlink(self):
        strWarning = _("You can only delete data on draft state")
        for record in self:
            if record.state != "draft":
                if not self.env.context.get("force_unlink", False):
                    raise UserError(strWarning)
        _super = super(LeaseOperatingCommon, self)
        _super.unlink()

    @api.multi
    def validate_tier(self):
        _super = super(LeaseOperatingCommon, self)
        _super.validate_tier()
        for record in self:
            if record.validated:
                record.action_approve()

    @api.multi
    def restart_validation(self):
        _super = super(LeaseOperatingCommon, self)
        _super.restart_validation()
        for record in self:
            record.request_validation()

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            if record.name == "/":
                name = "*" + str(record.id)
            else:
                name = record.name
            result.append((record.id, name))
        return result
