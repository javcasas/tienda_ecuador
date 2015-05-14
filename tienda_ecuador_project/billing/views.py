from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseForbidden
from models import Item, Bill, BillItem, CompanyUser, Company, Customer
from forms import ItemForm, BillForm, BillItemForm
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


class CompanySelectedMixin(View):
    """
    Base class for views where the company has been already selected
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
        def wrapper(request, company_id, *args, **kwargs):
            get_object_or_404(
                CompanyUser, user=request.user, company_id=company_id
            )
            return fn(request, company_id, *args, **kwargs)
        return wrapper

    @classmethod
    def as_view(cls, **initkwargs):
        """
        Generates a view
        """
        view = super(CompanySelectedMixin, cls).as_view(**initkwargs)
        return cls.has_access_to_company(view)

    @classmethod
    def prepare_base_param_dict(cls, fn):
        """
        Makes self.base_param_dict
        """
        @wraps(fn)
        def wrapper(self, request, company_id):
            self._base_param_dict = {
                'company_id': company_id,
                'company': get_object_or_404(Company, id=company_id),
            }
            return fn(self, request, company_id)
        return wrapper

    @property
    def base_param_dict(self):
        return self._base_param_dict.copy()


class BillSelectedMixin(CompanySelectedMixin):
    """
    Base class for views where the company and bill have been already selected
    """
    @classmethod
    def prepare_base_param_dict(cls, fn):
        """
        Makes self.base_param_dict
        """
        @wraps(fn)
        def wrapper(self, request, company_id, bill_id, *args, **kwargs):
            self._base_param_dict = {
                'company_id': company_id,
                'company': get_object_or_404(Company, id=company_id),
                'bill_id': bill_id,
                'bill': get_object_or_404(Bill, id=bill_id,
                                          company_id=company_id),
            }
            return fn(self, request, company_id, bill_id, *args, **kwargs)
        return wrapper

    @classmethod
    def check_bill_can_be_modified(cls, fn):
        @wraps(fn)
        def wrapper(self, request, company_id, bill_id, *args, **kwargs):
            param_dict = self.base_param_dict
            if param_dict['bill'].can_be_modified():
                return fn(self, request, company_id, bill_id, *args, **kwargs)
            else:
                return HttpResponseForbidden("Bill is definitive")
        return wrapper


class BillItemSelectedMixin(BillSelectedMixin):
    """
    Base class for views where the company,
    bill and bill itemhave been already selected
    """
    @classmethod
    def prepare_base_param_dict(cls, fn):
        """
        Makes self.base_param_dict
        """
        @wraps(fn)
        def wrapper(self, request, company_id, bill_id, item_id):
            self._base_param_dict = {
                'company_id': company_id,
                'company': get_object_or_404(Company, id=company_id),
                'bill_id': bill_id,
                'bill': get_object_or_404(Bill, id=bill_id,
                                          company_id=company_id),
                'item_id': item_id,
                'item': get_object_or_404(BillItem, id=item_id,
                                          company_id=company_id,
                                          bill_id=bill_id),
            }
            return fn(self, request, company_id, bill_id, item_id)
        return wrapper


class ItemSelectedMixin(CompanySelectedMixin):
    """
    Base class for views where the company and item have been already selected
    """
    @classmethod
    def prepare_base_param_dict(cls, fn):
        """
        Makes self.base_param_dict
        """
        @wraps(fn)
        def wrapper(self, request, company_id, item_id):
            self._base_param_dict = {
                'company_id': company_id,
                'company': get_object_or_404(Company, id=company_id),
                'item_id': item_id,
                'item': get_object_or_404(Item, id=item_id,
                                          company_id=company_id),
            }
            return fn(self, request, company_id, item_id)
        return wrapper


class CompanyIndex(CompanySelectedMixin):
    @CompanySelectedMixin.prepare_base_param_dict
    def get(self, request, company_id):
        """
        Shows an index for a company
        """
        param_dict = self.base_param_dict
        param_dict['items'] = Item.objects.filter(company_id=company_id)
        param_dict['bills'] = Bill.objects.filter(company_id=company_id)
        param_dict['customers'] = Customer.objects.filter(company_id=company_id)
        return render(request, "billing/company_index.html", param_dict)


class ViewItem(ItemSelectedMixin):
    @ItemSelectedMixin.prepare_base_param_dict
    def get(self, request, company_id, item_id):
        """
        View an inventory item
        """
        return render(request, "billing/view_item.html", self.base_param_dict)


class EditItem(ItemSelectedMixin):
    template = "billing/edit_item.html"
    form_class = ItemForm

    @ItemSelectedMixin.prepare_base_param_dict
    def get(self, request, company_id, item_id):
        """
        Edit an inventory item
        """
        param_dict = self.base_param_dict
        param_dict['form'] = self.form_class(instance=param_dict['item'])
        return render(request, self.template, param_dict)

    @ItemSelectedMixin.prepare_base_param_dict
    def post(self, request, company_id, item_id):
        """
        Edit and submit an inventory item
        """
        param_dict = self.base_param_dict
        form = self.form_class(request.POST, instance=param_dict['item'])
        if form.is_valid():
            form.save(commit=True)
            return redirect("view_item", company_id, item_id)
        else:
            param_dict['form'] = form
            return render(request, self.template, param_dict)


class ViewBill(BillSelectedMixin):
    @BillSelectedMixin.prepare_base_param_dict
    def get(self, request, company_id, bill_id):
        """
        View a bill
        """
        return render(request, "billing/view_bill.html", self.base_param_dict)


class NewBill(CompanySelectedMixin):
    @CompanySelectedMixin.prepare_base_param_dict
    def post(self, request, company_id):
        """
        Create a new bill
        """
        customer, created = Customer.objects.get_or_create(
            name='Consumidor Final',
            company=self.base_param_dict['company'],
        )
        new = Bill(company_id=company_id, issued_to=customer)
        new.save()
        return redirect("view_bill", company_id, new.id)


class EditBill(BillSelectedMixin):
    template = "billing/edit_bill.html"
    form_class = BillForm

    @BillSelectedMixin.prepare_base_param_dict
    @BillSelectedMixin.check_bill_can_be_modified
    def get(self, request, company_id, bill_id):
        """
        Edit a bill
        """
        param_dict = self.base_param_dict
        param_dict['form'] = self.form_class(instance=param_dict['bill'])
        return render(request, self.template, param_dict)

    @BillSelectedMixin.prepare_base_param_dict
    @BillSelectedMixin.check_bill_can_be_modified
    def post(self, request, company_id, bill_id):
        """
        Edit and submit a bill
        """
        param_dict = self.base_param_dict
        form = self.form_class(request.POST, instance=param_dict['bill'])
        if form.is_valid():
            form.save(commit=True)
            return redirect("view_bill", company_id, bill_id)
        else:
            param_dict['form'] = form
            return render(request, self.template, param_dict)


class DeleteBill(BillSelectedMixin):
    @BillSelectedMixin.prepare_base_param_dict
    @BillSelectedMixin.check_bill_can_be_modified
    def post(self, request, company_id, bill_id):
        """
        Delete a bill
        """
        bill = self.base_param_dict['bill']
        for item in bill.items:
            item.delete()
        bill.delete()
        return redirect("company_index", company_id)


class AddItemToBill(BillSelectedMixin):
    form_class = BillItemForm
    template = "billing/add_item_to_bill.html"

    @BillSelectedMixin.prepare_base_param_dict
    @BillSelectedMixin.check_bill_can_be_modified
    def get(self, request, company_id, bill_id):
        """
        Add an item to a bill
        """
        param_dict = self.base_param_dict
        data = {
            'bill': bill_id,
            'company': company_id,
        }
        param_dict['form'] = self.form_class(data)
        return render(request, self.template, param_dict)

    @BillSelectedMixin.prepare_base_param_dict
    @BillSelectedMixin.check_bill_can_be_modified
    def post(self, request, company_id, bill_id):
        """
        Add an item and submit to a bill
        """
        param_dict = self.base_param_dict
        form = self.form_class(request.POST)
        if form.is_valid():
            form.save()
            return redirect("view_bill", company_id, bill_id)
        else:
            param_dict['form'] = form
            return render(request, self.template, param_dict)


class EditItemInBill(BillItemSelectedMixin):
    form_class = BillItemForm
    template = "billing/edit_item_in_bill.html"

    @BillItemSelectedMixin.prepare_base_param_dict
    @BillItemSelectedMixin.check_bill_can_be_modified
    def get(self, request, company_id, bill_id, item_id):
        """
        Edit an item in a bill
        """
        param_dict = self.base_param_dict
        form = self.form_class(instance=param_dict['item'])
        param_dict['form'] = form
        return render(request, self.template, param_dict)

    @BillItemSelectedMixin.prepare_base_param_dict
    @BillItemSelectedMixin.check_bill_can_be_modified
    def post(self, request, company_id, bill_id, item_id):
        """
        Edit an item and submit in a bill
        """
        param_dict = self.base_param_dict
        form = self.form_class(request.POST, instance=param_dict['item'])
        if form.is_valid():
            form.save()
            return redirect("view_bill", company_id, bill_id)
        else:
            param_dict['form'] = form
            return render(request, self.template, param_dict)


class DeleteItemFromBill(BillItemSelectedMixin):
    @BillItemSelectedMixin.prepare_base_param_dict
    @BillItemSelectedMixin.check_bill_can_be_modified
    def post(self, request, company_id, bill_id, item_id):
        """
        Delete an item from a bill
        """
        param_dict = self.base_param_dict
        param_dict['item'].delete()
        return redirect("view_bill", company_id, bill_id)
