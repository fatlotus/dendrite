import tkbackend

# Returns the preferred backend module.
# 
# This property must never change over the life of a running instance.
def preferred():
   return tkbackend