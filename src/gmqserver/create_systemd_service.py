import os
import shutil

from zmq_server import make_cmd_parser

# Template for what will be going into the
template = """
WantedBy=default.target

[Service]
WorkingDirectory={base_dir}
ExecStart=python run_server.py {config_path}
StandardError=journal
StandardOutput=journal

[Unit]
Description=Starting the gantry/periphary control message servers
"""


if __name__ == "__main__":
    parser = make_cmd_parser(
        "create_systemd_service.py",
        """
        Creating the files required to run a server instance as a user-level
        systemd service.
        """,
    )
    args = parser.parse_args()

    # Paths required to define the systemd services
    systemd_path = os.path.join(os.environ["HOME"], ".config/systemd/user")
    service_path = os.path.join(systemd_path, "gantrymq.service")
    final_config_file = os.path.join(
        os.environ["HOME"], ".config/gantrymq_server_config.json"
    )

    # Making the files
    os.makedirs(systemd_path, exist_ok=True)
    with open(service_path, "w") as f:
        f.write(template.format(base_dir=os.getcwd(), config_path=final_config_file))
    shutil.copy(args.config, final_config_file)

    # Printing the instruction message
    print(
        f"""
        Completed making the service files! Check the contents of
        [{service_path}] and [{final_config_file}].

        To stop the existing systemd-handled server (if it exists):

        > systemctl --user stop gantrymq.service

        To start the the systemd-handled server:

        > systemctl --user start gantrymq.service

        To check the status of the systemd-handled server:

        > systemctl --user status gantrymq.service
        """
    )
