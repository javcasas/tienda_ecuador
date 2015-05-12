from django.shortcuts import render, get_object_or_404, redirect
from models import Item, Bill, CompanyUser, Company
from forms import ItemForm  # , BillForm, BillItemForm
from django.contrib.auth.decorators import login_required
from functools import wraps


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
    }
    return render(request, "billing/view_item.html", param_dict)


@login_required
@has_access_to_company
def edit_item(request, company_id, item_id):
    """
    Edit and submit an inventory item
    """
    company = get_object_or_404(Company, id=company_id)
    item = get_object_or_404(Item, pk=item_id, company=company)
    if request.method == 'POST':
        form = ItemForm(request.POST, instance=item)
        if form.is_valid():
            form.save(commit=True)
            return redirect("view_item", company_id, item_id)
        else:
            print form.errors
    else:
        form = ItemForm(instance=item)
    param_dict = {
        'form': form,
        'item_id': item_id,
        'company_id': company_id,
    }
    return render(request, "billing/edit_item.html", param_dict)
#
#
# @login_required
# def view_bill(request, bill_id):
#    # bill = get_object_or_404(Bill, pk=bill_id)
#    # param_dict = {
#        # 'bill': bill,
#    # }
#    # return render(request, "billing/view_bill.html", param_dict)
#
#
# @login_required
# def new_bill(request):
#    # customer, created = Customer.objects.get_or_create(name='Consumidor Final')
#    # new = Bill(shop=get_shop(request), issued_to=customer)
#    # new.save()
#    # return redirect("view_bill", new.pk)
#
#
# @login_required
# def edit_bill(request, bill_id):
#    # bill = get_object_or_404(Bill, pk=bill_id, shop=get_shop(request))
#    # if not bill.can_be_modified():
#        # # The bill has been issued, and can't be modified
#        # raise Exception("The bill can't be modified")
#
#    # if request.method == 'POST':
#        # form = BillForm(request.POST, instance=bill)
#        # if form.is_valid():
#            # form.save(commit=True)
#            # return redirect("view_bill", bill_id)
#        # else:
#            # print form.errors
#    # else:
#        # form = BillForm(instance=bill)
#    # return render(request, "billing/edit_bill.html", {'form': form, 'bill_id': bill_id})
#
#
# @login_required
# def delete_bill(request, bill_id):
#    # bill = get_object_or_404(Bill, pk=bill_id, shop=get_shop(request))
#    # if request.method == 'POST':
#        # if bill.is_proforma:
#            # items = BillItem.objects.find(bill=bill)
#            # for item in items:
#                # item.delete()
#            # bill.delete()
#        # else:
#            # raise Exception("Bill is definitive")
#    # return redirect("index")
#
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
