Internal blender plugin used to batch convert weapons and cosmetics to be displayed on the Creators.TF loadout preview page.
Released for public use, output glb files should be usable in any engine that supports them.

# Requirements:
- Blender Source Tools
- Blender 2.8+

# Setup:
- Use included python scripts to sort and decompile all source assets (mdl and vtf)
- Install Blender Source Tools plugin.
- Install plugin
- Fill in plugin options for input folders and out folder paths.

# How to use:
Open Blender, File > Convert QCs.
Then wait for all to convert. If a .glb file exists already then it will be skipped.

Check output data.json for what was converted and their extra information. This extra information is intended to be added to the creators.tf economy data for each cosmetic/weapon.

For materials that have masks for tints, these masks are also generated and output.
