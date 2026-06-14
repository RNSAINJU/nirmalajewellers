from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms_page_images import CustomerPageImageForm
from .models import CustomerPageImage


@login_required(login_url='/accounts/login/')
def page_images_settings(request):
    """Manage customer storefront images (hero banners, etc.)."""
    slots = CustomerPageImage.all_slots()
    edit_slot = request.GET.get('slot')

    if request.method == 'POST':
        slot_key = request.POST.get('slot')
        page_image = get_object_or_404(CustomerPageImage, slot=slot_key)
        form = CustomerPageImageForm(request.POST, request.FILES, instance=page_image)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                f'Updated {page_image.get_slot_display()} successfully.',
            )
            return redirect(f'{request.path}?slot={slot_key}')
        edit_slot = slot_key
    else:
        form = None
        if edit_slot:
            page_image = get_object_or_404(CustomerPageImage, slot=edit_slot)
            form = CustomerPageImageForm(instance=page_image)

    context = {
        'page_title': 'Customer Page Images',
        'description': 'Upload and manage images shown on the public customer website.',
        'slots': slots,
        'edit_slot': edit_slot,
        'form': form,
        'slot_choices': CustomerPageImage.PageSlot.choices,
    }
    return render(request, 'main/page_images_settings.html', context)
