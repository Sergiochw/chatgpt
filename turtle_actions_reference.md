# Turtle Actions Reference

## Motion

| Method | Summary |
| --- | --- |
| ``forward`` | Move the turtle forward by the specified distance. |
| ``fd`` | Move the turtle forward by the specified distance. |
| ``backward`` | Move the turtle backward by distance. |
| ``bk`` | Move the turtle backward by distance. |
| ``back`` | Move the turtle backward by distance. |
| ``right`` | Turn turtle right by angle units. |
| ``rt`` | Turn turtle right by angle units. |
| ``left`` | Turn turtle left by angle units. |
| ``lt`` | Turn turtle left by angle units. |
| ``goto`` | Move turtle to an absolute position. |
| ``setpos`` | Move turtle to an absolute position. |
| ``setposition`` | Move turtle to an absolute position. |
| ``teleport`` | Teleport the turtle without drawing (requires Python 3.12+) |
| ``setx`` | Set the turtle's first coordinate to x. |
| ``sety`` | Set the turtle's second coordinate to y. |
| ``setheading`` | Set the orientation of the turtle to to_angle. |
| ``seth`` | Set the orientation of the turtle to to_angle. |
| ``home`` | Move turtle to the origin - coordinates (0,0). |
| ``circle`` | Draw a circle with given radius. |
| ``dot`` | Draw a dot with diameter size, using color. |
| ``stamp`` | Stamp a copy of the turtleshape onto the canvas and return its id. |
| ``clearstamp`` | Delete stamp with given stampid. |
| ``clearstamps`` | Delete all or first/last n of turtle's stamps. |
| ``undo`` | undo (repeatedly) the last turtle action. |
| ``speed`` | Return or set the turtle's speed. |

## State

| Method | Summary |
| --- | --- |
| ``position`` | Return the turtle's current location (x,y), as a Vec2D-vector. |
| ``pos`` | Return the turtle's current location (x,y), as a Vec2D-vector. |
| ``towards`` | Return the angle of the line from the turtle's position to (x, y). |
| ``xcor`` | Return the turtle's x coordinate. |
| ``ycor`` | Return the turtle's y coordinate. |
| ``heading`` | Return the turtle's current heading. |
| ``distance`` | Return the distance from the turtle to (x,y) in turtle step units. |

## Measurement

| Method | Summary |
| --- | --- |
| ``degrees`` | Set angle measurement units to degrees. |
| ``radians`` | Set the angle measurement units to radians. |

## Pen (drawing)

| Method | Summary |
| --- | --- |
| ``pendown`` | Pull the pen down -- drawing when moving. |
| ``pd`` | Pull the pen down -- drawing when moving. |
| ``down`` | Pull the pen down -- drawing when moving. |
| ``penup`` | Pull the pen up -- no drawing when moving. |
| ``pu`` | Pull the pen up -- no drawing when moving. |
| ``up`` | Pull the pen up -- no drawing when moving. |
| ``pensize`` | Set or return the line thickness. |
| ``width`` | Set or return the line thickness. |
| ``pen`` | Return or set the pen's attributes. |
| ``isdown`` | Return True if pen is down, False if it's up. |

## Pen (color)

| Method | Summary |
| --- | --- |
| ``color`` | Return or set the pencolor and fillcolor. |
| ``pencolor`` | Return or set the pencolor. |
| ``fillcolor`` | Return or set the fillcolor. |

## Pen (fill)

| Method | Summary |
| --- | --- |
| ``filling`` | Return fillstate (True if filling, False else). |
| ``begin_fill`` | Called just before drawing a shape to be filled. |
| ``end_fill`` | Fill the shape drawn after the call begin_fill(). |

## Pen (more)

| Method | Summary |
| --- | --- |
| ``reset`` | Delete the turtle's drawings and restore its default values. |
| ``clear`` | Delete the turtle's drawings from the screen. Do not move turtle. |
| ``write`` | Write text at the current turtle position. |

## Visibility

| Method | Summary |
| --- | --- |
| ``showturtle`` | Makes the turtle visible. |
| ``st`` | Makes the turtle visible. |
| ``hideturtle`` | Makes the turtle invisible. |
| ``ht`` | Makes the turtle invisible. |
| ``isvisible`` | Return True if the Turtle is shown, False if it's hidden. |

## Appearance

| Method | Summary |
| --- | --- |
| ``shape`` | Set turtle shape to shape with given name / return current shapename. |
| ``resizemode`` | Set resizemode to one of the values: "auto", "user", "noresize". |
| ``shapesize`` | Set/return turtle's stretchfactors/outline. Set resizemode to "user". |
| ``turtlesize`` | Set/return turtle's stretchfactors/outline. Set resizemode to "user". |
| ``shearfactor`` | Set or return the current shearfactor. |
| ``tiltangle`` | Set or return the current tilt-angle. |
| ``tilt`` | Rotate the turtleshape by angle. |
| ``shapetransform`` | Set or return the current transformation matrix of the turtle shape. |
| ``get_shapepoly`` | Return the current shape polygon as tuple of coordinate pairs. |

## Events

| Method | Summary |
| --- | --- |
| ``onclick`` | Bind fun to mouse-click event on this turtle on canvas. |
| ``onrelease`` | Bind fun to mouse-button-release event on this turtle on canvas. |
| ``ondrag`` | Bind fun to mouse-move event on this turtle on canvas. |

## Specials

| Method | Summary |
| --- | --- |
| ``begin_poly`` | Start recording the vertices of a polygon. |
| ``end_poly`` | Stop recording the vertices of a polygon. |
| ``get_poly`` | Return the lastly recorded polygon. |
| ``clone`` | Create and return a clone of the turtle. |
| ``getturtle`` | Return the Turtleobject itself. |
| ``getpen`` | Return the Turtleobject itself. |
| ``getscreen`` | Return the TurtleScreen object, the turtle is drawing  on. |
| ``setundobuffer`` | Set or disable undobuffer. |
| ``undobufferentries`` | Return count of entries in the undobuffer. |
