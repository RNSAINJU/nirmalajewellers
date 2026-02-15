# Photo Upload Guide for Nirmala Jewellers

## Where to Upload Photos

### 1. Ornament Photos (Product Images)

#### Through Django Admin Panel:
1. **Login to Admin Panel**: Navigate to `/admin/` and login with your credentials
2. **Access Ornaments**: Click on "Ornaments" in the admin panel
3. **Upload Photo**:
   - **For New Ornament**: Click "Add Ornament" button
     - Fill in ornament details (name, code, type, weight, etc.)
     - Scroll to the "Image" field
     - Click "Choose File" button
     - Select your photo from your computer
     - Click "Save" at the bottom
   
   - **For Existing Ornament**: 
     - Find the ornament in the list
     - Click on it to edit
     - Scroll to the "Image" field
     - Click "Choose File" to replace or add a photo
     - Click "Save"

#### Through Ornament Management Interface:
1. **Navigate to Ornaments**: From the dashboard sidebar, click "Ornaments" → "Ornament List"
2. **Edit Ornament**: Click the edit button (pencil icon) next to the ornament
3. **Upload Photo**: Use the image upload field to select and upload a photo
4. **Save Changes**: Click the save button

### 2. Photo Requirements

- **File Format**: JPG, JPEG, PNG
- **Recommended Size**: 
  - Minimum: 800x800 pixels
  - Maximum: 2000x2000 pixels for optimal quality
- **Aspect Ratio**: Square (1:1) or Portrait (3:4) works best
- **File Size**: Try to keep under 5MB for faster loading

### 3. Photo Storage

- All photos are stored in **Cloudinary** (cloud storage service)
- Photos are automatically organized in the `ornaments/` folder
- Cloudinary handles image optimization and delivery
- Photos are accessible via CDN for fast loading on the customer website

### 4. Best Practices

1. **Photo Quality**:
   - Use well-lit, high-resolution photos
   - Clean white or neutral background preferred
   - Multiple angles of the ornament are recommended

2. **Photo Naming**:
   - Use descriptive names like `gold-necklace-001.jpg`
   - Avoid spaces in file names (use hyphens or underscores)

3. **Bulk Upload**:
   - For uploading multiple ornaments with photos, use the "Create Multiple" feature
   - You can also import via Excel with image URLs

### 5. Customer Homepage Display

Photos uploaded will automatically appear on:
- Customer home page (New Arrivals section)
- Product detail pages
- Category pages
- Search results

### 6. Troubleshooting

**Photo not showing?**
- Check if the photo was successfully uploaded (look for the image preview)
- Verify the image file format is supported
- Try a smaller file size if upload fails
- Check your Cloudinary credentials in settings

**Photo looks distorted?**
- Ensure the original photo has good resolution
- Use square or portrait aspect ratio
- Avoid extreme wide or tall images

### 7. Technical Details

- **Storage Backend**: Cloudinary
- **Image Field**: CloudinaryField in Ornament model
- **Folder Structure**: `ornaments/` in Cloudinary
- **Configuration**: Set in `settings.py` with Cloudinary credentials

For any technical issues with photo uploads, contact the system administrator.
