import json, logging, os
from models import CommandsModel
from PIL import Image

def create_commands():
    try:
        with open('src/commands.json', 'r') as file:
            commands_data = json.load(file)
            # logging.info(f"commands.json file was loaded.")
    except FileNotFoundError:
        logging.error(f"Could not find commands.json file.")
        commands_data = {'commands': []}

    for single_command in commands_data['commands']:
        for single_command_single_prefix in single_command['prefix']:
            # Find if the command prfix exists
            cmd_query = CommandsModel.query.filter_by(prefix=single_command_single_prefix).first()
            if cmd_query:
                # If the command already exists, skip it
                # logging.info(f"Command already exists - {single_command_single_prefix}")
                pass
            else:
                # The class will automatically create the entry in the database
                new_command = CommandsModel.create_command(
                    category=single_command['category'],
                    prefix=single_command_single_prefix,
                    url=single_command['url'],
                    search_url=single_command.get('search_url'),
                    permission_name=single_command.get('permission_name', 'commands'),
                    permission_level=single_command.get('permission_level'),
                    is_command_for_sidebar=single_command.get('for_sidebar', False),
                    is_command_public=True
                )
                logging.info(f"Command {new_command.id} created successfully - '{new_command.prefix}' - Permission: {new_command.permission_name} - Level: {new_command.permission_level}")


def generate_logo_image(filename, size, icon_path = 'static/icon_rotated.png'):
    STATIC_FOLDER = os.path.join(os.getcwd(), 'static')
    if not os.path.exists(STATIC_FOLDER):
        os.makedirs(STATIC_FOLDER)

    # Open the icon image (your first letter logo "S" or other design)
    icon = Image.open(icon_path)
    
    # Resize the icon to match the desired size
    icon = icon.resize((size, size))
    
    # Create a new blank image with a transparent background
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    
    # Paste the icon onto the new blank image
    img.paste(icon, (0, 0), icon)  # Assuming the icon has transparency
    
    # Save the image to the static folder
    img.save(os.path.join(STATIC_FOLDER, filename))