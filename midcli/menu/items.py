import getpass

from midcli.gui.base.app import run_app
from midcli.gui.network.interface.list import NetworkInterfaceList
from midcli.utils.shell import spawn_shell


def _yesno(question):
    yesno = input(f"{question} (y/n) ")
    return yesno.lower().startswith("y")


def configure_network_interfaces(context):
    run_app(NetworkInterfaceList(context))


def reset_root_password(context):
    print("Changing password for root")
    print("This action will disable 2FA")
    print()

    while True:
        p1 = getpass.getpass()
        if not p1:
            print("Password change aborted.")
            return

        p2 = getpass.getpass("Retype password: ")
        if p1 != p2:
            print("Passwords do not match. Try again.")
            continue

        break

    print()
    with context.get_client() as c:
        user_id = c.call("user.query", [["username", "=", "root"]], {"get": True})["id"]
        c.call("user.update", user_id, {"password": p1})
        c.call("auth.twofactor.update", {"enabled": False})
    print("Password successfully changed.")


def reset_configuration(context):
    if _yesno("The configuration will be erased and reset to defaults. Are you sure?"):
        context.process_input("system config reset")


def cli(context):
    context.menu = False
    context.show_banner()


def shell(context):
    spawn_shell()


def reboot(context):
    if _yesno("Confirm reboot"):
        context.process_input("system reboot")


def shutdown(context):
    if _yesno("Confirm shutdown"):
        context.process_input("system shutdown")


menu_items = [
    ("Configure network interfaces", configure_network_interfaces),
    ("Reset root password", reset_root_password),
    ("Reset configuration to defaults", reset_configuration),
    ("Open TrueNAS CLI Shell", cli),
    ("Open Linux Shell", shell),
    ("Reboot", reboot),
    ("Shutdown", shutdown),
]


def process_menu_item(context, text):
    print()

    try:
        item = int(text.strip()) - 1
    except ValueError:
        return

    if not (0 <= item < len(menu_items)):
        return

    menu_items[item][1](context)
    print()
