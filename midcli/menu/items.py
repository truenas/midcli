import getpass
import json

from midcli.gui.base.app import run_app
from midcli.gui.network.configuration import NetworkConfiguration
from midcli.gui.network.interface.list import NetworkInterfaceList
from midcli.gui.network.static_route.list import StaticRouteList
from midcli.utils.shell import spawn_shell


def _yesno(question):
    yesno = input(f"{question} (y/n) ")
    return yesno.lower().startswith("y")


def configure_network_interfaces(context):
    run_app(NetworkInterfaceList(context))


def configure_network_settings(context):
    run_app(NetworkConfiguration(context))


def configure_static_routes(context):
    run_app(StaticRouteList(context))


def manage_local_administrator_password(context):
    with context.get_client() as c:
        local_administrators = c.call("privilege.local_administrators")

    user = None
    username = None
    if local_administrators:
        print("Please choose a local administrator to change password:\n")
        for i, user in enumerate(local_administrators):
            print(f"{i + 1}) {user['username']}")
        print()
        number = input(f"Enter an option from 1-{len(local_administrators)}: ")
        try:
            user = local_administrators[int(number) - 1]
        except (KeyError, ValueError):
            print("Invalid choice")
            return

        print(f"Changing password for {user['username']}")
        print("This action will disable 2FA")
        print()
    else:
        print("Please select Web UI authentication method:\n")
        print("1) Administrative user (admin)")
        print("2) Root user (not recommended)")
        print()
        number = input(f"Enter an option from 1-2: ")
        try:
            username = {"1": "admin", "2": "root"}[number]
        except KeyError:
            print("Invalid choice")
            return

        print(f"Setting up local administrator {username}")
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

    if user is not None:
        with context.get_client() as c:
            c.call("user.update", user["id"], {"password": p1})
            c.call("auth.twofactor.update", {"enabled": False})
        print("Password successfully changed.")
    elif username is not None:
        with context.get_client() as c:
            c.call("user.setup_local_administrator", username, p1)
        print("Local administrator successfully set up.")


def reset_configuration(context):
    if _yesno("The configuration will be erased and reset to defaults. Are you sure?"):
        context.process_input("system config reset")


def cli(context):
    context.menu = False
    context.show_banner()


def shell(context):
    spawn_shell()


def reboot(context):
    if reason := input("Please enter the reason for the system reboot: ").strip():
        with context.get_client() as c:
            c.call('system.reboot', json.dumps(reason))


def shutdown(context):
    if reason := input("Please enter the reason for the system shutdown: ").strip():
        with context.get_client() as c:
            c.call('system.shutdown', json.dumps(reason))


def get_menu_items(context):
    menu_items = [
        ("Configure network interfaces", configure_network_interfaces),
        ("Configure network settings", configure_network_settings),
        ("Configure static routes", configure_static_routes),
    ]
    with context.get_client() as c:
        if c.call("user.has_local_administrator_set_up"):
            menu_items.append(("Change local administrator password", manage_local_administrator_password))
        else:
            menu_items.append(("Set up local administrator", manage_local_administrator_password))
    menu_items += [
        ("Reset configuration to defaults", reset_configuration),
        ("Open TrueNAS CLI Shell", cli),
        ("Open Linux Shell", shell),
        ("Reboot", reboot),
        ("Shutdown", shutdown),
    ]
    return menu_items


def process_menu_item(context, menu_items, text):
    print()

    try:
        item = int(text.strip()) - 1
    except ValueError:
        return

    if not (0 <= item < len(menu_items)):
        return

    menu_items[item][1](context)
    print()
