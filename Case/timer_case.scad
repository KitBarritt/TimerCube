// Toast Timer Case — ESP32-S3-Matrix
// Prototype v1
// Outside: 40 × 40 × 40 mm
// LED matrix slot: 25.5 mm wide, 1.8 mm deep

include <BOSL2/std.scad>
include <BOSL2/screws.scad>
use <MCAD/boxes.scad>

/* ── parameters ─────────────────────────────────────────── */
outer     = 40;       // outer cube dimension (mm)
wall      = 2.0;      // wall thickness
floor_t   = 2.0;      // floor / lid thickness

matrix_w  = 25.8;     // matrix PCB width
slot_d    = 1.8;      // slot depth (holds matrix edge)
slot_t    = 1.0;      // slot wall thickness (rail width)
slot_h    = 32.0;      // slot wall thickness (rail width)

window_w  = 21.0;     // LED visible aperture width
window_h  = 22.0;     // LED visible aperture height

base_w    = 80;
base_h    = 4;

USB_w = 11;
USB_h = 5.2;
USB_z = 6;

print_t_base = 1;

$fn = 64; // Sets high resolution for the threads

// Create a block with a 3/8-16 female tripod hole
module tripod_base(offset){
    translate([offset, 20, 4])
        difference() {
            cube([40, 40, 8], center=true); // Your main part
            
    // screw_hole parameters:
    // "5/8-11" -> Standard large tripod/mic thread
    // l=22     -> Depth of the hole (slightly deeper than part)
    // thread=true -> Renders actual physical threads
    // $slop=0.2 -> 3D printing tolerance (increase to 0.3 if too tight)
            screw_hole("3/8-16", l=22, thread=true, anchor=CENTER, $slop=0.2);
            translate([0, 0, 2])
                cylinder(2, 5.5, 5.5);
    }
}
tripod_base(-25);

/* ── derived ─────────────────────────────────────────────── */
inner     = outer - 2*wall;
box_h     = outer;

module base(){
    translate([-base_w/4, -base_w/4, 0])
        cube([base_w, base_w, base_h]);
    
}

module lid(){
    cube([outer, outer, wall]);


    // interior
    translate([inner/2 + wall,inner/2 + 0.2, wall]) 
        //cube([inner, inner - wall - 0.5, wall]);
        roundedBox(size=[inner, inner - wall - 0.5, 2 * wall],radius=1, sidesonly=false);
}

module box_body(z_offset) {
    // Outer shell
    translate([0, 0, 8 * z_offset])
    {
        difference(){
            cube([outer, outer, box_h]);


            // hollow interior
            translate([wall, wall, floor_t])
                cube([inner, inner, box_h]);
            // Front window for LED matrix
            translate([(outer - window_w)/2, -0.1, (outer - window_h)/2])
                cube([window_w, wall + 0.2, window_h]);
        }
        translate([0, wall, 0])
            cube([outer, wall, outer]);
    }
}

module matrix_slots() {

    difference(){
        translate([0, wall, 0])
            cube([outer, wall, outer]);
        translate([(outer - matrix_w)/2, 1, (outer - window_h )/2])
            cube([matrix_w, wall + 0.2, slot_h+ 0.1]);
        translate([(outer - window_w)/2, 2, (outer - window_h)/2])
            cube([window_w, wall + 0.2, slot_h+ 0.1]);
    }
}

module window_cutout(){
    // Front window for LED matrix
    translate([(outer - window_w)/2, -0.1, (outer - window_h)/2])
        cube([window_w, wall + 0.2, window_h]);    
}

module slot_cutout(){
        // Slot cutout
        translate([(outer - matrix_w)/2, 1, (outer - window_h)/2 - 3])
            cube([matrix_w, wall + 0.2, slot_h + 2]);
        // Board cutout 1
        translate([(outer - window_w)/2, 2, (outer - window_h)/2])
            cube([window_w, wall + 0.2, slot_h+ 0.1]); 
         // Board cutout 2
        translate([(outer - matrix_w)/2, 2, (outer - 14)])
            cube([matrix_w, wall + 2, slot_h]);  
        // Component cutout
        translate([(outer - 8)/2, wall, 7])
            cube([8, wall + 2, 4]);  
}

module USB_cutout(){
    translate([(outer - USB_w)/2, outer - wall - 0.1, USB_z])
        cube([USB_w, 5, USB_h]);
    
}

/* ── assembly ────────────────────────────────────────────── */
//translate([0, 0, base_h]){
    difference(){
        box_body(0);
        slot_cutout();
        USB_cutout();
    }

//base();

//Lid
translate([outer + 5, 0, 0])
    lid();
    
