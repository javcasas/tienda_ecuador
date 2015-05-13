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


def has_access_to_company(fn):
    """
    Decorator that checks the current user can use the company specified
    by company_id
    """
    @wraps(fn)
    def wrapper(request, company_id, *args, **kwargs):
        get_object_or_404(
            CompanyUser, user=request.user, company_id=company_id
        )
        return fn(request, company_id, *args, **kwargs)
    return wrapper


@login_required
@has_access_to_company
def company_index(request, company_id):
    """
    Shows an index for a company
    """
    company = get_object_or_404(Company, id=company_id)
    items = Item.objects.filter(company=company)
    bills = Bill.objects.filter(company=company)
    param_dict = {
        'items': items,
        'bills': bills,
        'company_id': company_id,
    }
    return render(request, "billing/company_index.html", param_dict)


@login_required
@has_access_to_company
def view_item(request, company_id, item_id):
    """
    View an inventory item
    """
    company = get_object_or_404(Company, id=company_id)
    item = get_object_or_404(Item, pk=item_id, company=company)
    param_dict = {
        'company': company,
        'item': item,
        'company_id': company_id,
    }
    return render(request, "billing/view_item.html", param_dict)


class HasAccessToCompanyMixin(View):
    @classmethod
    def as_view(cls, **initkwargs):
        view = super(HasAccessToCompanyMixin, cls).as_view(**initkwargs)
        return has_access_to_company(view)


class ObjectEditView(HasAccessToCompanyMixin):
    def get(self, request, *args, **kwargs):
        """
        Implements the GET method, shows a form for the object
        """
        param_dict = self.base_param_dict(*args, **kwargs)
        item = self.get_object(*args, **kwargs)
        param_dict['form'] = self.form_class(instance=item)
        return render(request, self.template, param_dict)

    def post(self, request, *args, **kwargs):
        """
        Implements the POST method, checks the posted data
        and saves and redirects
        """
        param_dict = self.base_param_dict(*args, **kwargs)
        item = self.get_object(*args, **kwargs)
        form = self.form_class(request.POST, instance=item)
        if form.is_valid():
            form.save(commit=True)
            return self.success_url(*args, **kwargs)
        else:
            param_dict['form'] = form
            return render(request, self.template, param_dict)


class EditItem(ObjectEditView):
    template = "billing/edit_item.html"
    form_class = ItemForm

    def get_object(self, company_id, item_id):
        return get_object_or_404(Item, id=item_id, company_id=company_id)

    def base_param_dict(self, company_id, item_id):
        return {
            'item_id': item_id,
            'company_id': company_id,
        }

    def success_url(self, company_id, item_id):
        return redirect("view_item", company_id, item_id)


@login_required
@has_access_to_company
def view_bill(request, company_id, bill_id):
    bill = get_object_or_404(Bill, pk=bill_id, company_id=company_id)
    param_dict = {
        'bill': bill,
        'company_id': company_id,
    }
    return render(request, "billing/view_bill.html", param_dict)


class NewBill(HasAccessToCompanyMixin):
    def post(self, request, company_id):
        customer, created = Customer.objects.get_or_create(
            name='Consumidor Final'
        )
        new = Bill(company_id=company_id, issued_to=customer)
        new.save()
        return redirect("view_bill", company_id, new.pk)


class EditBill(ObjectEditView):
    template = "billing/edit_bill.html"
    form_class = BillForm

    def get_object(self, company_id, bill_id):
        return get_object_or_404(Bill, id=bill_id, company_id=company_id)

    def base_param_dict(self, company_id, bill_id):
        return {
            'bill_id': bill_id,
            'company_id': company_id,
        }

    def success_url(self, company_id, bill_id):
        '''
        What to do when save is successful
        '''
        return redirect("view_bill", company_id, bill_id)

    def post(self, request, company_id, bill_id):
        '''
        Custom POST to check if bill.can_be_modified
        '''
        bill = self.get_object(company_id, bill_id)
        if not bill.can_be_modified():
            # The bill has been issued, and can't be modified
            return HttpResponseForbidden("Bill is definitive")

        form = self.form_class(request.POST, instance=bill)
        if form.is_valid():
            form.save(commit=True)
            return self.success_url(company_id, bill_id)
        param_dict = self.base_param_dict(company_id, bill_id)
        param_dict['form'] = form,
        return render(request, self.template, param_dict)


class DeleteBill(HasAccessToCompanyMixin):
    def post(self, request, company_id, bill_id):
        bill = get_object_or_404(Bill, pk=bill_id, company_id=company_id)
        if bill.is_proforma:
            for item in BillItem.objects.filter(bill=bill):
                item.delete()
            bill.delete()
        else:
            return HttpResponseForbidden("Bill is definitive")
        return redirect("company_index", company_id)


class AddItemToBill(HasAccessToCompanyMixin):
    form_class = BillItemForm
    def get(self, request, company_id, bill_id):
        bill = get_object_or_404(Bill, id=bill_id, company_id=company_id)
        if not bill.can_be_modified():
            # The bill has been issued, and can't be modified
            return HttpResponseForbidden("Bill is definitive")

        data = {
            'bill': bill_id,
            'company': company_id,
        }
        form = self.form_class(data)
        field_dict = {
            'company_id': company_id,
            'bill_id': bill_id,
            'form': form,
            'bill': bill,
        }
        return render(request, "billing/add_item_to_bill.html", field_dict)

    def post(self, request, company_id, bill_id):
        bill = get_object_or_404(Bill, id=bill_id, company_id=company_id)
        if not bill.can_be_modified():
            # The bill has been issued, and can't be modified
            return HttpResponseForbidden("Bill is definitive")

        form = self.form_class(request.POST)
        if form.is_valid():
            form.save()
            return redirect("view_bill", company_id, bill_id)
        else:
            field_dict = {
                'company_id': company_id,
                'bill_id': bill_id,
                'form': form,
                'bill': bill,
            }
            return render(request, "billing/add_item_to_bill.html", field_dict)

class EditItemInBill(HasAccessToCompanyMixin):
    form_class = BillItemForm
    def get(self, request, company_id, bill_id, item_id):
        item = get_object_or_404(BillItem, id=item_id, company_id=company_id, bill_id=bill_id)
        bill = get_object_or_404(Bill, id=bill_id, company_id=company_id)
        if not bill.can_be_modified():
            # The bill has been issued, and can't be modified
            return HttpResponseForbidden("Bill is definitive")

        form = self.form_class(instance=item)
        field_dict = {
            'company_id': company_id,
            'bill_id': bill_id,
            'item_id': item_id,
            'form': form,
            'bill': bill,
            'item': item,
        }
        return render(request, "billing/edit_item_in_bill.html", field_dict)

    def post(self, request, company_id, bill_id, item_id):
        bill = get_object_or_404(Bill, id=bill_id, company_id=company_id)
        bill_item = get_object_or_404(BillItem, bill_id=bill_id, company_id=company_id, id=item_id)
        if not bill.can_be_modified():
            # The bill has been issued, and can't be modified
            return HttpResponseForbidden("Bill is definitive")

        form = self.form_class(request.POST, instance=bill_item)
        if form.is_valid():
            form.save()
            return redirect("view_bill", company_id, bill_id)
        else:
            field_dict = {
                'company_id': company_id,
                'bill_id': bill_id,
                'form': form,
                'bill': bill,
            }
            return render(request, "billing/add_item_to_bill.html", field_dict)
# @login_required
# def add_item_to_bill(request, bill_id):
#    # bill = get_object_or_404(Bill, pk=bill_id, shop=get_shop(request))
#    # if not bill.can_be_modified():
#        # # The bill has been issued, and can't be modified
#        # raise Exception("The bill can't be modified")
#
#    # if request.method == 'POST':
#        # item = Item.objects.get(pk=request.POST['item_id'], shop=get_shop(request))
#        # values = dict(item.__dict__)
#        # for k in values.keys():
#            # if k.startswith('_') or k in ('id', 'baseitem_ptr_id'):
#                # values.pop(k)
#        # values['qty'] = 1
#        # values['bill'] = bill
#        # bitem = BillItem(**values)
#        # bitem.save()
#        # return redirect("view_bill", bill_id)
#    # items = Item.objects.filter(shop=get_shop(request))
#    # return render(request, "billing/add_item_to_bill.html", {'bill': bill, 'items': items})
#
#
# def edit_item_in_bill(request, bill_id, item_id):
#    # bill = get_object_or_404(Bill, pk=bill_id, shop=get_shop(request))
#    # item = get_object_or_404(BillItem, pk=item_id, bill=bill, shop=get_shop(request))
#    # if not bill.can_be_modified():
#        # # The bill has been issued, and can't be modified
#        # raise Exception("The bill can't be modified")
#
#    # if request.method == 'POST':
#        # form = BillItemForm(request.POST, instance=item)
#        # if form.is_valid():
#            # form.save(commit=True)
#            # return redirect("view_bill", bill_id)
#        # else:
#            # print form.errors
#    # else:
#        # form = BillItemForm(instance=item)
#    # return render(request, "billing/edit_item_in_bill.html", {'form': form, 'bill_id': bill_id})
#
# def delete_item_in_bill(request, bill_id, item_id):
#    # bill = get_object_or_404(Bill, pk=bill_id, shop=get_shop(request))
#    # item = get_object_or_404(BillItem, pk=item_id, bill=bill, shop=get_shop(request))
#    # if not bill.can_be_modified():
#        # # The bill has been issued, and can't be modified
#        # raise Exception("The bill can't be modified")
#
#    # if request.method == 'POST':
#        # item.delete()
#    # return redirect("view_bill", bill_id)
