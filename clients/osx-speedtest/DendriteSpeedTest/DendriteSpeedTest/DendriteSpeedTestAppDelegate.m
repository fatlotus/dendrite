//
//  DendriteSpeedTestAppDelegate.m
//  DendriteSpeedTest
//
//  Created by Jeremy Archer on 8/10/11.
//  Copyright 2011 University of Chicago CI. All rights reserved.
//

#include <sys/resource.h>
#import "DendriteSpeedTestAppDelegate.h"

@implementation DendriteSpeedTestAppDelegate

@synthesize window;

- (void)applicationDidFinishLaunching:(NSNotification *)aNotification
{
    struct rlimit limits;
    
    getrlimit(RLIMIT_NOFILE, &limits);
    
    NSLog(@"limits: (soft=%llu, hard=%llu)", limits.rlim_cur, limits.rlim_max);
    
    [testRunner initializeUI];
}

@end
