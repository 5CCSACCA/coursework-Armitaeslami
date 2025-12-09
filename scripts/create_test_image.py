#!/usr/bin/env python3
"""
Generate a simple test image for API testing.
This creates a basic image with colored shapes that YOLO might detect patterns in.
"""

import os

try:
    from PIL import Image, ImageDraw
except ImportError:
    print("Installing Pillow...")
    os.system("pip install pillow")
    from PIL import Image, ImageDraw


def create_test_image(output_path: str = "examples/test_image.jpg"):
    """Create a simple test image with shapes."""
    
    # Create a new image with white background
    width, height = 640, 480
    image = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(image)
    
    # Draw a blue sky
    draw.rectangle([0, 0, width, height//2], fill='skyblue')
    
    # Draw green grass
    draw.rectangle([0, height//2, width, height], fill='lightgreen')
    
    # Draw a simple house (rectangle + triangle roof)
    house_left = 100
    house_right = 250
    house_top = 200
    house_bottom = 350
    
    # House body
    draw.rectangle([house_left, house_top, house_right, house_bottom], fill='brown', outline='black')
    
    # Roof
    roof_points = [
        (house_left - 20, house_top),
        (house_right + 20, house_top),
        ((house_left + house_right) // 2, house_top - 80)
    ]
    draw.polygon(roof_points, fill='darkred', outline='black')
    
    # Door
    door_width = 30
    door_height = 60
    door_left = (house_left + house_right) // 2 - door_width // 2
    draw.rectangle([door_left, house_bottom - door_height, door_left + door_width, house_bottom], 
                   fill='sienna', outline='black')
    
    # Window
    window_size = 40
    window_left = house_left + 20
    window_top = house_top + 30
    draw.rectangle([window_left, window_top, window_left + window_size, window_top + window_size],
                   fill='lightblue', outline='black')
    
    # Draw a simple car
    car_left = 350
    car_bottom = 380
    
    # Car body
    draw.rectangle([car_left, car_bottom - 40, car_left + 120, car_bottom], fill='red', outline='black')
    draw.rectangle([car_left + 20, car_bottom - 70, car_left + 100, car_bottom - 35], fill='red', outline='black')
    
    # Windows
    draw.rectangle([car_left + 25, car_bottom - 65, car_left + 55, car_bottom - 40], fill='lightblue')
    draw.rectangle([car_left + 60, car_bottom - 65, car_left + 95, car_bottom - 40], fill='lightblue')
    
    # Wheels
    draw.ellipse([car_left + 10, car_bottom - 15, car_left + 40, car_bottom + 15], fill='black')
    draw.ellipse([car_left + 80, car_bottom - 15, car_left + 110, car_bottom + 15], fill='black')
    
    # Draw a simple tree
    tree_x = 520
    tree_bottom = 350
    
    # Trunk
    draw.rectangle([tree_x - 10, tree_bottom - 60, tree_x + 10, tree_bottom], fill='saddlebrown')
    
    # Leaves (circles)
    draw.ellipse([tree_x - 40, tree_bottom - 120, tree_x + 40, tree_bottom - 40], fill='darkgreen')
    
    # Draw sun
    sun_x, sun_y = 550, 60
    sun_radius = 40
    draw.ellipse([sun_x - sun_radius, sun_y - sun_radius, 
                  sun_x + sun_radius, sun_y + sun_radius], fill='yellow')
    
    # Add some clouds
    cloud_y = 80
    for cloud_x in [100, 280]:
        draw.ellipse([cloud_x, cloud_y, cloud_x + 60, cloud_y + 30], fill='white')
        draw.ellipse([cloud_x + 30, cloud_y - 10, cloud_x + 90, cloud_y + 25], fill='white')
        draw.ellipse([cloud_x + 50, cloud_y, cloud_x + 110, cloud_y + 30], fill='white')
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
    
    # Save the image
    image.save(output_path, 'JPEG', quality=95)
    print(f"✅ Test image created: {output_path}")
    print(f"   Size: {width}x{height}")
    print(f"   Format: JPEG")
    
    return output_path


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate test image for API testing")
    parser.add_argument("-o", "--output", default="examples/test_image.jpg",
                        help="Output path for the test image")
    args = parser.parse_args()
    
    create_test_image(args.output)
    
    print("\n📝 Usage:")
    print(f"   curl -X POST http://localhost:8000/detect \\")
    print(f"     -H 'Authorization: Bearer test-token' \\")
    print(f"     -F 'file=@{args.output}'")


if __name__ == "__main__":
    main()
