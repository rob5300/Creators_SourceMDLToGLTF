Internal blender plugin used to batch convert weapons and cosmetics to be displayed on the Creators.TF loadout preview page.
Rleased for public use.

# Requirements:
- Blender Source Tools
- Blender 2.8+

# Setup:
- Use included python scripts to sort and decompile all source assets (mdl and vtf)

Put all these paths into the corrisponding variables in the plugin options in blender.
Also fill in the output folder.

# How to use:
Install Blender Source Tools plugin.
Install plugin, Open Blender, File > Convert QCs.
Then wait for all to convert. If a .glb file exists already then it will be skipped. Check output data.json for what was converted and their extra information.
