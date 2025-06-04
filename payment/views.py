from django.db import IntegrityError
from django.shortcuts import render
from .utils import bind_card_init, bind_card_confirm, pay_create, pay_pre_apply, pay_apply, PaymentError, save, \
   user_by_id, singer_get_by_id, purchase_create, delete, purchase_accept
from .tasks import register_schedule
from django.utils.translation import gettext as _
from .models import SingerModel
from itertools import batched

router = Router()


class BindCardStates(StatesGroup):
    card_number = State()
    expiry = State()
    initial = State()
    confirmation = State()


class PayByCardStates(StatesGroup):
    card_number = State()
    expiry = State()
    otp = State()
    confirmation = State()


def payment_view(request):
    return render(request, 'payment.html')

@router.callback_query(F.data.startswith("start_pay_by_sms:"))
async def start_pay_by_sms(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    singer_id = int(callback.data.split(":")[1])
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text=_("🔙 Back to singer"), callback_data=f"pay:{singer_id}")
    msg = await callback.message.answer(
        _("Please send me your card number!\nexample: 1234123412341234 or 1234 1234 1234 1234"),
        reply_markup=keyboard.as_markup()
    )
    await callback.message.delete()
    await state.set_state(PayByCardStates.card_number)
    await state.update_data(msg=msg)
    await state.update_data(singer_id=singer_id)

@router.message(PayByCardStates.card_number)
async def process_card_number_sms(message: types.Message, state: FSMContext):
    data = await state.get_data()
    if prev_msg := data.get('msg'):
        try:
            await prev_msg.delete()
        except:
            pass
    card_number = message.text.replace(" ", "")
    if len(card_number) != 16 or not card_number.isdigit():
        msg = await message.answer(_("Invalid card number, please send me a valid card number."))
        await state.update_data(msg=msg)
        return await message.delete()
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text=_("🔙 Back to singer"), callback_data=f"pay:{data.get('singer_id')}")
    msg = await message.answer(
        _("Now enter the card expiration date\nexample: 10/30 1030"),
        reply_markup=keyboard.as_markup()
    )
    try:
        await message.delete()
    except:
        pass
    await state.set_state(PayByCardStates.expiry)
    await state.update_data(msg=msg)
    await state.update_data(card_number=card_number)

@router.message(PayByCardStates.expiry)
async def process_expiry_sms(message: types.Message, state: FSMContext):
    data = await state.get_data()
    if prev_msg := data.get('msg'):
        try:
            await prev_msg.delete()
        except:
            pass
    expiry = message.text.replace("/", "")
    if len(expiry) != 4 or not expiry.isdigit():
        msg = await message.answer(_("Invalid expiration date, please send me a valid expiration date."))
        return await state.update_data(msg=msg)
    expiry = expiry[2:] + expiry[:2]
    exists, user = await user_by_id(message.from_user.id)
    if not exists:
        await message.answer(_("Lets authorize now! Press /start"))
        try:
            await message.delete()
        finally:
            return
    try:
        singer = await singer_get_by_id(int(data["singer_id"]))
    except SingerModel.DoesNotExist:
        await message.answer(_("Sorry, the singer you entered doesn't exist."))
        try:
            await message.delete()
        finally:
            return
    purchase = await purchase_create(user=user, singer=singer, price=singer.price)
    msg = await message.answer(_("Sending sms..."))
    try:
        await message.delete()
    except:
        pass
    try:
        transaction_id = await pay_create(int(purchase.price * 100), purchase.id)
    except PaymentError as e:
        await msg.edit_text(e.message)
        return
    except Exception as err:
        print(err)
        await msg.edit_text(_("Sorry, unexpected error, please try again later."))
        await delete(purchase)
        await state.clear()
        return
    try:
        await pay_pre_apply(transaction_id, card_number=data["card_number"], card_expiry=int(expiry))
    except PaymentError as err:
        await msg.edit_text(err.message)
        return
    except Exception as err:
        print(err)
        await msg.answer(_("Sorry, unexpected error, please try again later."))
        await delete(purchase)
        await state.clear()
        return
    await msg.edit_text(_("Please send me otp code"))
    await state.update_data(msg=msg)
    await state.update_data(singer=singer)
    await state.update_data(purchase=purchase)
    await state.update_data(transaction_id=transaction_id)
    await state.set_state(PayByCardStates.confirmation)

@router.message(PayByCardStates.confirmation)
async def process_confirmation_sms(message: types.Message, state: FSMContext):
    exists, user = await user_by_id(message.from_user.id)
    if not exists:
        await message.answer(_("You are not authorized!"))
        await message.delete()
        await state.clear()
        return
    otp = message.text
    data = await state.get_data()
    if prev_msg := data.get('msg'):
        try:
            await prev_msg.delete()
        except:
            pass
    transaction_id = data['transaction_id']
    purchase = data['purchase']
    if not otp.isdigit():
        await message.answer(_("Incorrect code please try again."))
        return
    try:
        await pay_apply(transaction_id, int(otp))
    except PaymentError as err:
        await message.answer(err.message)
        if err.code != 'STPIMS-ERR-098':
            await state.clear()
            await delete(purchase)
        await message.delete()
        return
    except Exception as err:
        print(err)
        await message.answer(_("Sorry, unexpected error, please try again later."))
        await state.clear()
        await message.delete()
        return
    await purchase_accept(purchase)
    msg = await message.answer(_("Payment was successful."))
    await send_invite_link(msg, data.get('singer'))
    await state.clear()

@router.callback_query(F.data == "start_card_bind")
async def start_card_bind(callback: types.CallbackQuery, state: FSMContext):
    exists, user = await user_by_id(callback.from_user.id)
    if not exists:
        await callback.answer(_("You are not authorized to bind a card"))
        await callback.message.answer(_("Lets authorize now! Press /start"))
        await callback.message.delete()
        return
    await callback.answer(_("Let's start binding your card"))
    msg = await callback.message.answer(_("Please send me your card number!\nexample: 1234123412341234 or 1234 1234 1234 1234"))
    await callback.message.delete()
    await state.set_state(BindCardStates.card_number)
    await state.update_data(msg=msg)

@router.message(BindCardStates.card_number)
async def process_card_number(message: types.Message, state: FSMContext):
    prev_msg = (await state.get_data())['msg']
    if prev_msg:
        try:
            await prev_msg.delete()
        except:
            pass
    card_number = message.text.replace(" ", "")
    if len(card_number) != 16 or not card_number.isdigit():
        await message.answer(_("Invalid card number, please send me a valid card number."))
        return await message.delete()
    msg = await message.answer(_("Now enter the card expiration date\nexample: 10/30 1030"))
    await message.delete()
    await state.update_data(card_number=card_number)
    await state.update_data(msg=msg)
    await state.set_state(BindCardStates.expiry)

@router.message(BindCardStates.expiry)
async def process_expiry(message: types.Message, state: FSMContext):
    data = await state.get_data()
    if prev_msg := data.get('msg'):
        try:
            await prev_msg.delete()
        except: ...
    expiry = message.text.replace("/", "")
    if len(expiry) != 4 or not expiry.isdigit():
        await message.answer(_("Invalid expiration date, please send me a valid expiration date."))
        return await message.delete()
    expiry = expiry[2:] + expiry[:2]
    keyboard = InlineKeyboardBuilder()
    keyboard.row(InlineKeyboardButton(text=_("confirm"), callback_data="bind_card"))
    keyboard.row(InlineKeyboardButton(text=_("edit"), callback_data="start_card_bind"))
    keyboard.adjust(1)
    await message.answer(
        _("Please confirm your card information:\nNumber: {0}\nExpiry: {1}")
        .format(data['card_number'], message.text),
        reply_markup=keyboard.as_markup()
    )
    await message.delete()
    await state.update_data(expiry=expiry)
    await state.set_state(BindCardStates.initial)

@router.callback_query(F.data == "bind_card", BindCardStates.initial)
async def process_card_bind_init(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    data = await state.get_data()
    try:
        transaction_id = await bind_card_init(data['card_number'], data["expiry"])
    except PaymentError as err:
        await callback.message.answer(err.message)
        if err.code != 'STPIMS-ERR-098':
            await state.clear()
        await callback.message.delete()
        return
    except Exception as err:
        print(err)
        await callback.answer(_("Sorry, unexpected error, please try again."))
        await callback.message.delete()
        await state.clear()
        return
    msg = await callback.message.answer(_("Send me confirmation code from message"))
    await callback.message.delete()
    await state.update_data(msg=msg)
    await state.update_data(transaction_id=transaction_id)
    await state.set_state(BindCardStates.confirmation)

@router.message(BindCardStates.confirmation)
async def process_card_confirm(message: types.Message, state: FSMContext):
    exists, user = await user_by_id(message.from_user.id)
    if not exists:
        await message.answer(_("You are not authorized to bind a card"))
        await message.delete()
        await state.clear()
        return
    data = await state.get_data()
    if prev_msg := data.get("msg"):
        try:
            await prev_msg.delete()
        except: ...
    try:
        card = await bind_card_confirm(data['transaction_id'], message.text, user.id)
    except PaymentError as err:
        await message.answer(err.message)
        if err.code != 'STPIMS-ERR-098':
            await state.clear()
        await message.delete()
        return
    except IntegrityError:
        await message.answer(_("Card already exists"))
        await message.delete()
        await state.clear()
        return
    except Exception as err:
        print(err)
        await message.answer(_("Invalid confirmation code, please send me a valid confirmation code."))
        await state.clear()
        return await message.delete()
    await save(card)
    await message.answer(_("Binding was successful."))
    await message.delete()
    await state.clear()

@router.callback_query(F.data.startswith("schedule:"))
async def process_schedule(callback: types.CallbackQuery, state: FSMContext):
    exists, user = await user_by_id(callback.from_user.id)
    if not exists:
        await callback.answer(_("You are not authorized to bind a card"))
        await callback.message.edit_text(_("Lets authorize now! Press /start"))
        return
    if not get_user_card(user):
        await callback.answer(_("Sorry, you have no cards to schedule payment."))
        await callback.message.delete()
        return
    await callback.answer()
    await callback.message.answer("You can manage schedules by command /schedules")
    parts = callback.data.split(":")
    if parts[1] == "yes":
        register_schedule.delay(user.id, int(parts[-1]))
        await callback.message.edit_text(_("Successfully scheduled payment"))
    else:
        await callback.message.delete()

@router.message(Command("schedules"))
async def manage_schedules(message: types.Message, state: FSMContext):
    template = "payment-schedule-{}"
    exists, user = await user_by_id(message.from_user.id)
    if not exists:
        await message.answer(_("Lets authorize now! Press /start"))
        await message.delete()
        return
    if not await get_user_card(user):
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text=_("Bind card for pay"), callback_data=f"start_card_bind")
        await message.answer(_("If you will bind card press the button"), reply_markup=keyboard.as_markup())
        await message.delete()
        return
    schedules = await get_user_schedules()
    keyboard = InlineKeyboardBuilder()
    for schedule_group in batched(schedules, 2):
        keyboard.row(*(InlineKeyboardButton(text=schedule[0], callback_data=f"show_schedule:{schedules[1]}") for schedule in schedule_group))
    keyboard.button(text=_("+ new"), callback_data=f"register_new_schedule")
    await message.answer(_("Singers you have scheduled payment\nIf you will stop the schedule press the button"), reply_markup=keyboard.as_markup())

@router.callback_query(F.data.startswith("register_new_schedule"))
async def register_new_schedule(callback: types.CallbackQuery, state: FSMContext):
    exists, user = await user_by_id(callback.from_user.id)
    if not exists:
        await callback.answer(_("You are not authorized to bind a card"))
        await callback.message.edit_text(_("Lets authorize now! Press /start"))
        return
    await callback.answer()
    page = 0
    if ':' in callback.data:
        page = int(callback.data.split(':')[1])
    text, markup = await show_singer_selection("schedule:yes", host="register_new_schedule", only_not_available=True, user=user, page=page)
    await callback.message.edit_text(text, reply_markup=markup)
