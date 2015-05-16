from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseForbidden, QueryDict
from models import Item, Bill, BillItem, CompanyUser, Company, Customer
from forms import ItemForm, BillForm, BillItemForm, CustomerForm
from django.contrib.auth.decorators import login_required
from functools import wraps
from django.views.generic import View


@login_required
def index(request):
    """
    Shows an index for the current user,
    showing the companies he can administer
    If there is a single company,
    it redirects to the company automatically
    """
    c_user = CompanyUser.objects.filter(user=request.user)
    if len(c_user) == 1:
        return redirect("company_index", c_user[0].company.id)
    param_dict = {
        'companies': Company.objects.filter(id__in=[cu.id for cu in c_user]),
    }
    return render(request, "billing/index.html", param_dict)

def has_access_to_company(fn):
    """
    Decorator that checks the current user can use the company specified
    by company_id
    """
    @login_required
    @wraps(fn)
    def wrapper(request, **kwargs):
        company_id = kwargs.get('company_id')
        if company_id:
            get_object_or_404(
                CompanyUser, user=request.user, company_id=company_id
            )
        return fn(request, **kwargs)
    return wrapper

class BillingView(View):
    """
    Base class for views
    Checks:
        * That the user has access to the company
    """
    @classmethod
    def has_access_to_company(cls, fn):
        """
        Decorator that checks the current user can use the company specified
        by company_id
        """
        @login_required
        @wraps(fn)
        def wrapper(request, **kwargs):
            company_id = kwargs.get('company_id')
            if company_id:
                get_object_or_404(
                    CompanyUser, user=request.user, company_id=company_id
                )
            return fn(request, **kwargs)
        return wrapper

    def prepare_base_param_dict(self, request, **kwargs):
        """
        Makes self.base_param_dict
        """
        company_id = kwargs.get('company_id')
        bill_id = kwargs.get('bill_id')
        item_id = kwargs.get('item_id')
        param_dict = {}
        self._base_param_dict = param_dict
        if company_id:
            get_object_or_404(  # Ensure has access to the company
                CompanyUser, user=request.user, company_id=company_id)
            param_dict['company_id'] = company_id
            param_dict['company'] = get_object_or_404(Company, id=company_id)
            if bill_id:
                param_dict['bill_id'] = bill_id
                param_dict['bill'] = get_object_or_404(Bill, id=bill_id, company_id=company_id)
                if item_id:
                    param_dict['item_id'] = item_id
                    param_dict['item'] = get_object_or_404(BillItem, id=item_id, bill_id=bill_id),
            elif item_id:
                param_dict['item_id'] = item_id
                param_dict['item'] = get_object_or_404(Item, id=item_id, company_id=company_id)

    def dispatch(self, request, *args, **kwargs):
        self.prepare_base_param_dict(request, **kwargs)
        return super(BillingView, self).dispatch(request, *args, **kwargs)

    @classmethod
    def as_view(cls, **initkwargs):
        """
        Generates a view
        """
        view = super(BillingView, cls).as_view(**initkwargs)
        view = has_access_to_company(view)
        return view

    @property
    def base_param_dict(self):
        return self._base_param_dict.copy()


class CompanyIndex(BillingView):
    def get(self, request, company_id):
        """
        Shows an index for a company
        """
        param_dict = self.base_param_dict
        param_dict['items'] = Item.objects.filter(company_id=company_id)
        param_dict['bills'] = Bill.objects.filter(company_id=company_id)
        param_dict['customers'] = Customer.objects.filter(company_id=company_id)
        return render(request, "billing/company_index.html", param_dict)


class ItemView(BillingView):
    def get(self, request, company_id, item_id=None):
        """
        View an inventory item
        """
        return render(request, "billing/item_view.html", self.base_param_dict)

    def post(self, request, company_id, item_id=None):
        """
        Create or update an inventory item
        """
        data = request.POST.copy()
        data['company'] = company_id
        form = ItemForm(data)
        if form.is_valid():
            new = form.save()
            return redirect('item_view', company_id, new.id)
        else:
            param_dict = self.base_param_dict
            param_dict['form'] = form
            return render(request, 'billing/edit_item.html', param_dict)

    def put(self, request, company_id, item_id):
        """
        update an inventory item
        """
        data = QueryDict(request.body).copy()
        data['company'] = company_id
        instance = get_object_or_404(Item, id=item_id, company=company_id)
        form = ItemForm(data, instance=instance)
        if form.is_valid():
            form.save()
            return redirect('item_view', company_id, item_id)
        else:
            print form.errors
            param_dict = self.base_param_dict
            param_dict['form'] = form
            return render(request, 'billing/edit_item.html', param_dict)

    def delete(self, request, company_id, item_id):
        """
        delete an inventory item
        """
        self.base_param_dict['item'].delete()
        return redirect('item_index', company_id)


# class EditItem(ItemSelectedMixin):
    # template = "billing/edit_item.html"
    # form_class = ItemForm
# 
    # @ItemSelectedMixin.prepare_base_param_dict
    # def get(self, request, company_id, item_id):
        # """
        # Edit an inventory item
        # """
        # param_dict = self.base_param_dict
        # param_dict['form'] = self.form_class(instance=param_dict['item'])
        # return render(request, self.template, param_dict)
# 
    # @ItemSelectedMixin.prepare_base_param_dict
    # def post(self, request, company_id, item_id):
        # """
        # Edit and submit an inventory item
        # """
        # param_dict = self.base_param_dict
        # form = self.form_class(request.POST, instance=param_dict['item'])
        # if form.is_valid():
            # form.save(commit=True)
            # return redirect("view_item", company_id, item_id)
        # else:
            # param_dict['form'] = form
            # return render(request, self.template, param_dict)
# 
# 
# class ViewBill(BillSelectedMixin):
    # @BillSelectedMixin.prepare_base_param_dict
    # def get(self, request, company_id, bill_id):
        # """
        # View a bill
        # """
        # return render(request, "billing/view_bill.html", self.base_param_dict)
# 
# 
# class NewBill(CompanySelectedMixin):
    # @CompanySelectedMixin.prepare_base_param_dict
    # def post(self, request, company_id):
        # """
        # Create a new bill
        # """
        # customer, created = Customer.objects.get_or_create(
            # name='Consumidor Final',
            # company=self.base_param_dict['company'],
        # )
        # new = Bill(company_id=company_id, customer_name=customer.name)
        # new.save()
        # return redirect("view_bill", company_id, new.id)
# 
# 
# class EditBill(BillSelectedMixin):
    # template = "billing/edit_bill.html"
    # form_class = BillForm
# 
    # @BillSelectedMixin.prepare_base_param_dict
    # @BillSelectedMixin.check_bill_can_be_modified
    # def get(self, request, company_id, bill_id):
        # """
        # Edit a bill
        # """
        # param_dict = self.base_param_dict
        # param_dict['form'] = self.form_class(instance=param_dict['bill'])
        # return render(request, self.template, param_dict)
# 
    # @BillSelectedMixin.prepare_base_param_dict
    # @BillSelectedMixin.check_bill_can_be_modified
    # def post(self, request, company_id, bill_id):
        # """
        # Edit and submit a bill
        # """
        # param_dict = self.base_param_dict
        # form = self.form_class(request.POST, instance=param_dict['bill'])
        # if form.is_valid():
            # form.save(commit=True)
            # return redirect("view_bill", company_id, bill_id)
        # else:
            # param_dict['form'] = form
            # return render(request, self.template, param_dict)
# 
# 
# class DeleteBill(BillSelectedMixin):
    # @BillSelectedMixin.prepare_base_param_dict
    # @BillSelectedMixin.check_bill_can_be_modified
    # def post(self, request, company_id, bill_id):
        # """
        # Delete a bill
        # """
        # bill = self.base_param_dict['bill']
        # for item in bill.items:
            # item.delete()
        # bill.delete()
        # return redirect("company_index", company_id)
# 
# 
# class AddItemToBill(BillSelectedMixin):
    # form_class = BillItemForm
    # template = "billing/add_item_to_bill.html"
# 
    # @BillSelectedMixin.prepare_base_param_dict
    # @BillSelectedMixin.check_bill_can_be_modified
    # def get(self, request, company_id, bill_id):
        # """
        # Add an item to a bill
        # """
        # param_dict = self.base_param_dict
        # data = {
            # 'bill': bill_id,
            # 'company': company_id,
        # }
        # param_dict['form'] = self.form_class(data)
        # return render(request, self.template, param_dict)
# 
    # @BillSelectedMixin.prepare_base_param_dict
    # @BillSelectedMixin.check_bill_can_be_modified
    # def post(self, request, company_id, bill_id):
        # """
        # Add an item and submit to a bill
        # """
        # param_dict = self.base_param_dict
        # form = self.form_class(request.POST)
        # if form.is_valid():
            # form.save()
            # return redirect("view_bill", company_id, bill_id)
        # else:
            # param_dict['form'] = form
            # return render(request, self.template, param_dict)
# 
# 
# class EditItemInBill(BillItemSelectedMixin):
    # form_class = BillItemForm
    # template = "billing/edit_item_in_bill.html"
# 
    # @BillItemSelectedMixin.prepare_base_param_dict
    # @BillItemSelectedMixin.check_bill_can_be_modified
    # def get(self, request, company_id, bill_id, item_id):
        # """
        # Edit an item in a bill
        # """
        # param_dict = self.base_param_dict
        # form = self.form_class(instance=param_dict['item'])
        # param_dict['form'] = form
        # return render(request, self.template, param_dict)
# 
    # @BillItemSelectedMixin.prepare_base_param_dict
    # @BillItemSelectedMixin.check_bill_can_be_modified
    # def post(self, request, company_id, bill_id, item_id):
        # """
        # Edit an item and submit in a bill
        # """
        # param_dict = self.base_param_dict
        # form = self.form_class(request.POST, instance=param_dict['item'])
        # if form.is_valid():
            # form.save()
            # return redirect("view_bill", company_id, bill_id)
        # else:
            # param_dict['form'] = form
            # return render(request, self.template, param_dict)
# 
# 
# class DeleteItemFromBill(BillItemSelectedMixin):
    # @BillItemSelectedMixin.prepare_base_param_dict
    # @BillItemSelectedMixin.check_bill_can_be_modified
    # def post(self, request, company_id, bill_id, item_id):
        # """
        # Delete an item from a bill
        # """
        # param_dict = self.base_param_dict
        # param_dict['item'].delete()
        # return redirect("view_bill", company_id, bill_id)
# 
# 
# class NewCustomer(CompanySelectedMixin):
    # form_class = CustomerForm
# 
    # @CompanySelectedMixin.prepare_base_param_dict
    # def get(self, request, company_id):
        # """
        # Shows a form to create new customers
        # """
        # param_dict = self.base_param_dict
        # param_dict['new'] = True
        # data = {
            # 'company': company_id,
        # }
        # param_dict['form'] = self.form_class(data)
        # return render(request, "billing/edit_customer.html", param_dict)
# 
    # @CompanySelectedMixin.prepare_base_param_dict
    # def post(self, request, company_id):
        # """
        # Accepts submit
        # """
        # form = self.form_class(request.POST)
        # if form.is_valid():
            # form.save()
            # return redirect("company_index", company_id)
        # else:
            # param_dict = self.base_param_dict
            # param_dict['form'] = form
            # return render(request, "billing/edit_customer.html", param_dict)
