#    Author: Leonardo Pistone
#    Copyright 2015 Camptocamp SA
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

from openerp.tests.common import TransactionCase


class TestIntCreateTwoInvoices(TransactionCase):

    def test_so_and_po_on_delivery_creates_two_invoices(self):
        self.so.order_policy = 'picking'
        self.so.action_button_confirm()

        po = self.so.procurement_group_id.procurement_ids.purchase_id
        self.assertTrue(po)
        po.invoice_method = 'picking'
        po.signal_workflow('purchase_confirm')

        picking = po.picking_ids
        self.assertEqual(1, len(picking))
        picking.action_done()

        wizard = self.Wizard.with_context({
            'active_id': picking.id,
            'active_ids': [picking.id],
        }).create({})
        invoice_ids = wizard.create_invoice()
        invoices = self.env['account.invoice'].browse(invoice_ids)
        self.assertEqual(2, len(invoices))
        invoices = invoices.sorted(key=lambda r: r.type)

        self.assertEqual('in_invoice', invoices[0].type)
        self.assertEqual(po.partner_id, invoices[0].partner_id)

        self.assertEqual('out_invoice', invoices[1].type)
        self.assertEqual(self.customer, invoices[1].partner_id)

        # make sure the partner check does not pass trivially
        self.assertNotEqual(invoices[0].partner_id, invoices[1].partner_id)

        self.assertEqual(invoices[0], po.invoice_ids)
        self.assertEqual(invoices[1], self.so.invoice_ids)

    def test_so_on_delivery_creates_correct_invoice(self):
        self.so.order_policy = 'picking'
        self.so.action_button_confirm()

        po = self.so.procurement_group_id.procurement_ids.purchase_id
        self.assertTrue(po)
        po.signal_workflow('purchase_confirm')

        picking = po.picking_ids
        self.assertEqual(1, len(picking))
        picking.action_done()

        wizard = self.Wizard.with_context({
            'active_id': picking.id,
            'active_ids': [picking.id],
        }).create({})
        invoice_ids = wizard.create_invoice()
        invoices = self.env['account.invoice'].browse(invoice_ids)
        self.assertEqual(1, len(invoices))
        self.assertEqual(invoices.type, 'out_invoice')

        self.assertEqual(invoices, self.so.invoice_ids)
        self.assertEqual(1, len(po.invoice_ids))
        self.assertNotEqual(invoices, po.invoice_ids)

    def test_po_on_delivery_creates_correct_invoice(self):
        self.so.action_button_confirm()

        po = self.so.procurement_group_id.procurement_ids.purchase_id
        self.assertTrue(po)
        po.invoice_method = 'picking'
        po.signal_workflow('purchase_confirm')

        picking = po.picking_ids
        self.assertEqual(1, len(picking))
        picking.action_done()

        wizard = self.Wizard.with_context({
            'active_id': picking.id,
            'active_ids': [picking.id],
        }).create({})
        invoice_ids = wizard.create_invoice()
        invoices = self.env['account.invoice'].browse(invoice_ids)
        self.assertEqual(1, len(invoices))
        self.assertEqual(invoices.type, 'in_invoice')

        self.assertEqual(0, len(self.so.invoice_ids))
        self.assertEqual(invoices, po.invoice_ids)

    def setUp(self):
        super(TestIntCreateTwoInvoices, self).setUp()
        self.Wizard = self.env['stock.invoice.onshipping']

        self.customer = self.env.ref('base.res_partner_3')
        product = self.env.ref('product.product_product_36')
        dropship_route = self.env.ref('stock_dropshipping.route_drop_shipping')

        self.so = self.env['sale.order'].create({
            'partner_id': self.customer.id,
        })
        self.sol = self.env['sale.order.line'].create({
            'name': '/',
            'order_id': self.so.id,
            'product_id': product.id,
            'route_id': dropship_route.id,
        })
