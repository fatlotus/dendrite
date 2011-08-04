//
//  BlockingTestHelper.m
//  DendriteClient
//
//  Created by Jeremy Archer on 7/29/11.
//  Copyright 2011 University of Chicago CI. All rights reserved.
//

#import "BlockingTestHelper.h"

#define kBlockingNoticeTimeout @"timeout"
#define kBlockingNoticeSuccess @"success"
#define kBlockingNoticeNone nil

@interface BlockingTestHelper (hidden)

- (void)timeoutBlockingWait:(NSString*)event;

@end

@implementation BlockingTestHelper

@synthesize timeout;

- (id)init
{
    self = [super init];
    
    if (self != nil) {
        timeout = (NSTimeInterval)(15.0);
        firedEvents = [[NSMutableDictionary alloc] initWithCapacity:10];
    }
    
    return self;
}

- (void)timeoutBlockingWait:(NSString*)event
{
    [firedEvents setObject:kBlockingNoticeTimeout forKey:event];
}

- (void)waitForEvent:(NSString*)event {
    NSRunLoop * currentRunLoop = [NSRunLoop currentRunLoop];
    
    if (timeout > 0)
        [self performSelector:@selector(timeoutBlockingWait:) withObject:event afterDelay:timeout];
    
    while ([firedEvents objectForKey:event] == kBlockingNoticeNone && [currentRunLoop runMode:NSDefaultRunLoopMode beforeDate:[NSDate distantFuture]]) {
        
    }
    
    NSString * eventStatus = [firedEvents objectForKey:event];
    
    if (![eventStatus isEqualToString:kBlockingNoticeSuccess]) {
        [NSException raise:@"TestFailure" format:@"Waiting for event \"%@\" timed out.", event];
    }
}

- (void)triggerEvent:(NSString*)event
{
    [firedEvents setObject:kBlockingNoticeSuccess forKey:event];
}

@end
