//
//  DendriteSpeedTestAppDelegate.h
//  DendriteSpeedTest
//
//  Created by Jeremy Archer on 8/10/11.
//  Copyright 2011 University of Chicago CI. All rights reserved.
//

#import <Cocoa/Cocoa.h>
#import "DendriteTestRunner.h"

@interface DendriteSpeedTestAppDelegate : NSObject <NSApplicationDelegate> {
    NSWindow *window;
    IBOutlet DendriteTestRunner * testRunner;
}

@property (assign) IBOutlet NSWindow *window;

@end
