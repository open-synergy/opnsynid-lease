# Copyright 2019 OpenSynergy Indonesia
# Copyright 2020 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import _, api, fields, models
from openerp.exceptions import Warning as UserError


class LeaseOperatingScheduleCommon(models.AbstractModel):
    _name = "lease.operating_schedule_common"
    _description = "Abstract Model for Operating Lease Payment Schedule"

    @api.multi
    def _compute_lease_state(self):
        for document in self:
            document.amortization_state = document.amortization_id.state

    lease_id = fields.Many2one(
        string="# Operating Lease",
        comodel_name="lease.operating_common",
        ondelete="cascade",
    )
    date_start = fields.Date(
        string="Start Date",
        required=True,
    )
    date_end = fields.Date(
        string="End Date",
        required=True,
    )
    amount = fields.Float(
        string="Amount",
        required=True,
    )
    move_id = fields.Many2one(
        string="# Revenue/Expense Move",
        comodel_name="account.move",
        readonly=True,
    )
    invoice_id = fields.Many2one(
        string="# Invoice",
        comodel_name="account.invoice",
        readonly=True,
    )
    lease_state = fields.Selection(
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
        readonly=True,
    )

    @api.multi
    def action_create_account_move(self):
        for document in self:
            document._create_accrue_account_move()

    @api.multi
    def action_delete_account_move(self):
        for document in self:
            document._delete_accrue_account_move()

    @api.multi
    def action_create_invoice(self):
        for document in self:
            document._create_invoice()

    @api.multi
    def action_delete_invoice(self):
        for document in self:
            document._delete_invoice()

    @api.multi
    def _create_invoice(self):
        self.ensure_one()
        obj_invoice = self.env["account.invoice"]
        invoice = obj_invoice.create(self._prepare_invoice_data())
        self.write(
            {
                "invoice_id": invoice.id,
            }
        )

    @api.multi
    def _delete_invoice(self):
        self.ensure_one()
        invoice = self.invoice_id
        self.write(
            {
                "invoice_id": False,
            }
        )
        invoice.unlink()

    @api.multi
    def _get_invoice_journal(self):
        self.ensure_one()
        lease = self.lease_id
        result = lease.invoice_journal_id

        if not result:
            err_msg = _("No invoice journal defined")
            raise UserError(err_msg)

        return result

    @api.multi
    def _get_invoice_account(self):
        self.ensure_one()
        lease = self.lease_id
        result = lease.invoice_account_id

        if not result:
            if type.direction == "out":
                err_msg = _("No account receivable defined")
            else:
                err_msg = _("No account payable defined")
            raise UserError(err_msg)

        return result

    @api.multi
    def _get_invoice_line_account(self):
        self.ensure_one()

        type = self.lease_id.type_id
        lease = self.lease_id

        if type.lease_payment_time == "advance":
            result = lease.accrue_account_id
        else:
            result = lease.account_id

        if not result:
            if type.direction == "out":
                if type.lease_payment_time == "advance":
                    err_msg = _("No accrue revenue account defined")
                else:
                    err_msg = _("No revenue account defined")
            else:
                if type.lease_payment_time == "advance":
                    err_msg = _("No accrue expense account defined")
                else:
                    err_msg = _("No expense account defined")
            raise UserError(err_msg)

        return result

    @api.multi
    def _get_invoice_date(self):
        self.ensure_one()
        type = self.lease_id.type_id
        if type.lease_payment_time == "advance":
            return self.date_start
        else:
            return self.date_end

    @api.multi
    def _prepare_lease_invoice_line_data(self):
        self.ensure_one()
        account = self._get_invoice_line_account()
        return {
            "name": "name",  # TODO
            "product_id": False,  # TODO
            "account_id": account.id,
            "price_unit": self.amount,
            "quantity": 1.0,
            "uos_id": False,  # TODO
            "invoice_line_tax_id": False,  # TODO
        }

    @api.multi
    def _get_invoice_type(self):
        self.ensure_one()
        type = self.lease_id.type_id
        if type.direction == "out":
            return "out_invoice"
        else:
            return "in_invoice"

    @api.multi
    def _prepare_invoice_data(self):
        self.ensure_one()
        journal = self._get_invoice_journal()
        account = self._get_invoice_account()
        date_invoice = self._get_invoice_date()
        type = self._get_invoice_type()
        currency = self.lease_id.currency_id
        lines = []
        lines.append((0, 0, self._prepare_lease_invoice_line_data()))
        return {
            "partner_id": self.lease_id.partner_id.id,
            "date_invoice": date_invoice,
            "journal_id": journal.id,
            "account_id": account.id,
            "currency_id": currency.id,
            "origin": self.lease_id.name,
            "name": self.lease_id.name,  # TODO
            "type": type,
            "invoice_line": lines,
        }

    @api.multi
    def _create_accrue_account_move(self):
        self.ensure_one()

        obj_move = self.env["account.move"]
        data = self._prepare_accrue_account_move()
        # raise UserError(str(data))
        move = obj_move.create(data)
        self.write({"move_id": move.id})

    @api.multi
    def _delete_accrue_account_move(self):
        self.ensure_one()

        move = self.move_id
        self.write(
            {
                "move_id": False,
            }
        )
        move.unlink()

    @api.multi
    def _prepare_accrue_account_move(self):
        self.ensure_one()
        journal = self._get_move_journal()
        lines = []
        obj_period = self.env["account.period"]
        period_id = obj_period.find(self.date_start)[0].id
        lines.append((0, 0, self._prepare_debit_accrue_account_move_line()))
        lines.append((0, 0, self._prepare_credit_accrue_account_move_line()))
        return {
            "journal_id": journal.id,
            "date": self.date_start,
            "period_id": period_id,
            "ref": self.lease_id.name,
            "line_id": lines,
        }

    @api.multi
    def _prepare_accrue_account_move_line(self, account, debit, credit, partner=False):
        self.ensure_one()
        result = {
            "account_id": account.id,
            "name": "-",  # TODO,
            "partner_id": partner and partner.id or False,
            "debit": debit,
            "credit": credit,
        }
        return result

    @api.multi
    def _prepare_debit_accrue_account_move_line(self):
        self.ensure_one()
        account = self._get_accrue_debit_account()
        partner = self._get_accrue_debit_partner()
        data = self._prepare_accrue_account_move_line(
            account=account,
            debit=self.amount,
            credit=0.0,
            partner=partner,
        )
        return data

    @api.multi
    def _prepare_credit_accrue_account_move_line(self):
        self.ensure_one()
        account = self._get_accrue_credit_account()
        partner = self._get_accrue_credit_partner()
        data = self._prepare_accrue_account_move_line(
            account=account,
            debit=0.0,
            credit=self.amount,
            partner=partner,
        )
        return data

    @api.multi
    def _get_accrue_debit_account(self):
        self.ensure_one()
        lease = self.lease_id
        type = lease.type_id
        if type.direction == "out":
            result = lease.accrue_account_id
            err_msg = _("No accrue income account defined")
        else:
            err_msg = _("No expense account defined")
            result = lease.account_id

        if not result:
            raise UserError(err_msg)

        return result

    @api.multi
    def _get_accrue_credit_account(self):
        self.ensure_one()
        lease = self.lease_id
        type = lease.type_id
        if type.direction == "out":
            result = lease.account_id
            err_msg = _("No income account defined")
        else:
            err_msg = _("No accrue expense account defined")
            result = lease.accrue_account_id

        if not result:
            raise UserError(err_msg)

        return result

    @api.multi
    def _get_accrue_debit_partner(self):
        self.ensure_one()
        lease = self.lease_id
        type = lease.type_id
        result = False
        if type.direction == "out":
            result = lease.partner_id
        return result

    @api.multi
    def _get_accrue_credit_partner(self):
        self.ensure_one()
        lease = self.lease_id
        type = lease.type_id
        result = False
        if type.direction == "in":
            result = lease.partner_id
        return result

    @api.multi
    def _get_move_journal(self):
        self.ensure_one()
        result = self.lease_id.accrue_journal_id
        return result

    #
    # @api.multi
    # def _remove_account_move(self):
    #     self.ensure_one()
    #     aml = self.amortization_id.move_line_id
    #     reconcile = aml.reconcile_id or aml.reconcile_partial_id or False
    #     if reconcile:
    #         move_lines = reconcile.line_id
    #         move_lines -= self.move_line_id
    #         reconcile.unlink()
    #
    #         if len(move_lines) >= 2:
    #             move_lines.reconcile_partial()
    #     move = self.move_id
    #     self.write({"move_line_id": False})
    #     move.unlink()
    #
    # @api.multi
    # def _create_account_move(self):
    #     self.ensure_one()
    #     obj_move = self.env["account.move"]
    #     obj_aml = self.env["account.move.line"]
    #     aml_to_be_reconcile = self.amortization_id.move_line_id
    #     move = obj_move.create(self._prepare_account_move())
    #     aml = obj_aml.create(self._prepare_amortization_aml(move))
    #     self.write({"move_line_id": aml.id})
    #     aml_to_be_reconcile += aml
    #     obj_aml.create(self._prepare_contra_amortization_aml(move))
    #     aml_to_be_reconcile.reconcile_partial()
    #     return move
    #
    # @api.multi
    # def _prepare_account_move(self):
    #     self.ensure_one()
    #     amortization = self.amortization_id
    #     obj_period = self.env["account.period"]
    #     period_id = obj_period.find(self.date)[0].id
    #     return {
    #         "journal_id": amortization.journal_id.id,
    #         "date": self.date,
    #         "period_id": period_id,
    #     }
    #
    # @api.multi
    # def _prepare_amortization_aml(self, move):
    #     self.ensure_one()
    #     debit, credit = self._get_aml_amount()
    #     amortization = self.amortization_id
    #     partner_id = amortization.move_line_id.partner_id and \
    #         amortization.move_line_id.partner_id.id or \
    #         False
    #     analytic_id = amortization.move_line_id.analytic_account_id and \
    #         amortization.move_line_id.analytic_account_id.id or \
    #         False
    #     return {
    #         "move_id": move.id,
    #         "name": _("Amortization"),
    #         "account_id": amortization.account_id.id,
    #         "debit": debit,
    #         "credit": credit,
    #         "partner_id": partner_id,
    #         "analytic_account_id": analytic_id,
    #     }
    #
    # @api.multi
    # def _prepare_contra_amortization_aml(self, move):
    #     self.ensure_one()
    #     debit, credit = self._get_aml_amount(True)
    #     amortization = self.amortization_id
    #     analytic_id = amortization.analytic_id and \
    #         amortization.analytic_id.id or \
    #         False
    #     return {
    #         "move_id": move.id,
    #         "name": _("Amortization"),
    #         "account_id": amortization.contra_account_id.id,
    #         "debit": debit,
    #         "credit": credit,
    #         "analytic_account_id": analytic_id,
    #     }
    #
    # @api.multi
    # def _get_aml_amount(self, contra=False):
    #     self.ensure_one()
    #     amortization = self.amortization_id
    #     direction = amortization.type_id.direction
    #     debit = credit = 0.0
    #     if direction == "dr":
    #         credit = self.amount
    #     else:
    #         debit = self.amount
    #
    #     if contra:
    #         debit, credit = credit, debit
    #
    #     return debit, credit
    #
    # @api.model
    # def cron_create_account_move(self):
    #     date_now = fields.Date.today()
    #     schedule_ids = self.search([
    #         ("amortization_id.state", "=", "open"),
    #         ("date", "=", date_now),
    #         ("state", "=", "draft")
    #     ])
    #     if schedule_ids:
    #         for schedule in schedule_ids:
    #             schedule.action_create_account_move()
