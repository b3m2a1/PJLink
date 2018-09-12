/*
 * Header for class PJLink_NativeLink
 * Translated directly from the original JLink one
 */

#include "Python.h"

#ifndef _Included_PJLink_NativeLink
#define _Included_PJLink_NativeLink
#ifdef __cplusplus
extern "C" {
#endif
#undef PJLink_DEBUGLEVEL
#define PJLink_DEBUGLEVEL 0L
/*
 * Class:     PJLink_NativeLink
 * Method:    MLInitialize
 * Signature: ()V
 */
//JNIEXPORT void JNICALL Java_PJLink_MLInitialize
//  (JNIEnv *, jclass);
static PyObject *PJLink_MLInitialize
    ( PyObject *, PyObject * );

/*
 * Class:     PJLink_NativeLink
 * Method:    MLOpenString
 * Signature: (Ljava/lang/String;[Ljava/lang/String;)J
 */
//JNIEXPORT jlong JNICALL Java_PJLink_MLOpenString
//  (JNIEnv *, jobject, jstring, jobjectArray);
static PyObject *PJLink_MLOpenString
    ( PyObject *, PyObject *);

/*
 * Class:     PJLink_NativeLink
 * Method:    MLOpen
 * Signature: (I[Ljava/lang/String;[Ljava/lang/String;)J
 */
//JNIEXPORT jlong JNICALL Java_PJLink_MLOpen
//  (JNIEnv *, jobject, jint, jobjectArray, jobjectArray);
static PyObject *PJLink_MLOpen
    ( PyObject *, PyObject * );

/*
 * Class:     PJLink_NativeLink
 * Method:    MLLoopbackOpen
 * Signature: ([Ljava/lang/String;)J
 */
//JNIEXPORT jlong JNICALL Java_PJLink_MLLoopbackOpen
//  (JNIEnv *, jclass, jobjectArray);
static PyObject *PJLink_MLLoopbackOpen
    ( PyObject *, PyObject * );

/*
 * Class:     PJLink_NativeLink
 * Method:    MLSetEnvIDString
 * Signature: (Ljava/lang/String;)V
 */
//JNIEXPORT void JNICALL Java_PJLink_MLSetEnvIDString
//  (JNIEnv *, jclass, jstring);
//static PyObject *PJLink_MLSetEnvIDString
//    ( PyObject *, PyObject *);

/*
 * Class:     PJLink_NativeLink
 * Method:    MLGetLinkedEnvIDString
 * Signature: (J)Ljava/lang/String;
 */
//JNIEXPORT jstring JNICALL Java_PJLink_MLGetLinkedEnvIDString
//  (JNIEnv *, jclass, jlong);
//static PyObject *PJLink_MLGetLinkedEnvIDString
//    ( PyObject *, PyObject *);

/*
 * Class:     PJLink_NativeLink
 * Method:    MLConnect
 * Signature: (J)V
 */
//JNIEXPORT void JNICALL Java_PJLink_MLConnect
//  (JNIEnv *, jclass, jlong);
static PyObject *PJLink_MLConnect
    ( PyObject *, PyObject *);

/*
 * Class:     PJLink_NativeLink
 * Method:    MLClose
 * Signature: (J)V
 */
//JNIEXPORT void JNICALL Java_PJLink_MLClose
//  (JNIEnv *, jclass, jlong);
static PyObject *PJLink_MLClose
    ( PyObject *, PyObject *);

/*
 * Class:     PJLink_NativeLink
 * Method:    MLName
 * Signature: (J)Ljava/lang/String;
 */
//JNIEXPORT jstring JNICALL Java_PJLink_MLName
//  (JNIEnv *, jclass, jlong);
static PyObject *PJLink_MLName
    ( PyObject *, PyObject *);

/*
 * Class:     PJLink_NativeLink
 * Method:    MLNewPacket
 * Signature: (J)V
 */
//JNIEXPORT void JNICALL Java_PJLink_MLNewPacket
//  (JNIEnv *, jclass, jlong);
static PyObject *PJLink_MLNewPacket
    ( PyObject *, PyObject *);

/*
 * Class:     PJLink_NativeLink
 * Method:    MLNextPacket
 * Signature: (J)I
 */
//JNIEXPORT jint JNICALL Java_PJLink_MLNextPacket
//  (JNIEnv *, jclass, jlong);
static PyObject *PJLink_MLNextPacket
    ( PyObject *, PyObject *);

/*
 * Class:     PJLink_NativeLink
 * Method:    MLEndPacket
 * Signature: (J)V
 */
//JNIEXPORT void JNICALL Java_PJLink_MLEndPacket
//  (JNIEnv *, jclass, jlong);
static PyObject *PJLink_MLEndPacket
    ( PyObject *, PyObject *);

/*
 * Class:     PJLink_NativeLink
 * Method:    MLError
 * Signature: (J)I
 */
//JNIEXPORT jint JNICALL Java_PJLink_MLError
//  (JNIEnv *, jclass, jlong);
static PyObject *PJLink_MLError
    ( PyObject *, PyObject *);

/*
 * Class:     PJLink_NativeLink
 * Method:    MLClearError
 * Signature: (J)Z
 */
//JNIEXPORT jboolean JNICALL Java_PJLink_MLClearError
//  (JNIEnv *, jclass, jlong);
static PyObject *PJLink_MLClearError
    ( PyObject *, PyObject *);

/*
 * Class:     PJLink_NativeLink
 * Method:    MLErrorMessage
 * Signature: (J)Ljava/lang/String;
 */
//JNIEXPORT jstring JNICALL Java_PJLink_MLErrorMessage
//  (JNIEnv *, jclass, jlong);
static PyObject *PJLink_MLErrorMessage
    ( PyObject *, PyObject *);

/*
 * Class:     PJLink_NativeLink
 * Method:    MLSetError
 * Signature: (JI)V
 */
//JNIEXPORT void JNICALL Java_PJLink_MLSetError
//  (JNIEnv *, jclass, jlong, jint);
static PyObject *PJLink_MLSetError
    ( PyObject *, PyObject *);

/*
 * Class:     PJLink_NativeLink
 * Method:    MLReady
 * Signature: (J)Z
 */
//JNIEXPORT jboolean JNICALL Java_PJLink_MLReady
//  (JNIEnv *, jclass, jlong);
static PyObject *PJLink_MLReady
    ( PyObject *, PyObject *);

/*
 * Class:     PJLink_NativeLink
 * Method:    MLFlush
 * Signature: (J)V
 */
//JNIEXPORT void JNICALL Java_PJLink_MLFlush
//  (JNIEnv *, jclass, jlong);
static PyObject *PJLink_MLFlush
    ( PyObject *, PyObject *);

/*
 * Class:     PJLink_NativeLink
 * Method:    MLGetNext
 * Signature: (J)I
 */
//JNIEXPORT jint JNICALL Java_PJLink_MLGetNext
//  (JNIEnv *, jclass, jlong);
static PyObject *PJLink_MLGetNext
    ( PyObject *, PyObject *);

/*
 * Class:     PJLink_NativeLink
 * Method:    MLGetType
 * Signature: (J)I
 */
//JNIEXPORT jint JNICALL Java_PJLink_MLGetType
//  (JNIEnv *, jclass, jlong);
static PyObject *PJLink_MLGetType
    ( PyObject *, PyObject *);

/*
 * Class:     PJLink_NativeLink
 * Method:    MLPutNext
 * Signature: (JI)V
 */
//JNIEXPORT void JNICALL Java_PJLink_MLPutNext
//  (JNIEnv *, jclass, jlong, jint);
static PyObject *PJLink_MLPutNext
    ( PyObject *, PyObject *);

/*
 * Class:     PJLink_NativeLink
 * Method:    MLGetArgCount
 * Signature: (J)I
 */
//JNIEXPORT jint JNICALL Java_PJLink_MLGetArgCount
//  (JNIEnv *, jclass, jlong);
static PyObject *PJLink_MLGetArgCount
    ( PyObject *, PyObject *);

/*
 * Class:     PJLink_NativeLink
 * Method:    MLPutArgCount
 * Signature: (JI)V
 */
//JNIEXPORT void JNICALL Java_PJLink_MLPutArgCount
//  (JNIEnv *, jclass, jlong, jint);
static PyObject *PJLink_MLPutArgCount
    ( PyObject *, PyObject *);

/*
 * Class:     PJLink_NativeLink
 * Method:    MLPutData
 * Signature: (J[BI)V
 */
//JNIEXPORT void JNICALL Java_PJLink_MLPutData
//  (JNIEnv *, jclass, jlong, jbyteArray, jint);
static PyObject *PJLink_MLPutData
    ( PyObject *, PyObject *);

/*
 * Class:     PJLink_NativeLink
 * Method:    MLPutSize
 * Signature: (JI)V
 */
//JNIEXPORT void JNICALL Java_PJLink_MLPutSize
//  (JNIEnv *, jclass, jlong, jint);
static PyObject *PJLink_MLPutSize
    ( PyObject *, PyObject *);


/*
 * Class:     PJLink_NativeLink
 * Method:    MLGetData
 * Signature: (JI)[B
 */
//JNIEXPORT jbyteArray JNICALL Java_PJLink_MLGetData
//  (JNIEnv *, jclass, jlong, jint);
static PyObject *PJLink_MLGetData
    ( PyObject *, PyObject *);

/*
 * Class:     PJLink_NativeLink
 * Method:    MLBytesToGet
 * Signature: (J)I
 */
//JNIEXPORT jint JNICALL Java_PJLink_MLBytesToGet
//  (JNIEnv *, jclass, jlong);
static PyObject *PJLink_MLBytesToGet
    ( PyObject *, PyObject *);

/*
 * Class:     PJLink_NativeLink
 * Method:    MLBytesToPut
 * Signature: (J)I
 */
//JNIEXPORT jint JNICALL Java_PJLink_MLBytesToPut
//  (JNIEnv *, jclass, jlong);
static PyObject *PJLink_MLBytesToPut
    ( PyObject *, PyObject *);

/*
 * Class:     PJLink_NativeLink
 * Method:    MLGetString
 * Signature: (J)Ljava/lang/String;
 */
//JNIEXPORT jstring JNICALL Java_PJLink_MLGetString
//  (JNIEnv *, jclass, jlong);
static PyObject *PJLink_MLGetString
    ( PyObject *, PyObject *);

/*
 * Class:     PJLink_NativeLink
 * Method:    MLPutString
 * Signature: (JLjava/lang/String;)V
 */
//JNIEXPORT void JNICALL Java_PJLink_MLPutString
//  (JNIEnv *, jclass, jlong, jstring);
static PyObject *PJLink_MLPutString
    ( PyObject *, PyObject *);

/*
 * Class:     PJLink_NativeLink
 * Method:    MLGetByteString
 * Signature: (JB)[B
 */
//JNIEXPORT jbyteArray JNICALL Java_PJLink_MLGetByteString
//  (JNIEnv *, jclass, jlong, jbyte);
static PyObject *PJLink_MLGetByteString
    ( PyObject *, PyObject *);


/*
 * Class:     PJLink_NativeLink
 * Method:    MLPutByteString
 * Signature: (J[BI)V
 */
//JNIEXPORT void JNICALL Java_PJLink_MLPutByteString
//  (JNIEnv *, jclass, jlong, jbyteArray, jint);
static PyObject *PJLink_MLPutByteString
    ( PyObject *, PyObject *);

/*
 * Class:     PJLink_NativeLink
 * Method:    MLGetSymbol
 * Signature: (J)Ljava/lang/String;
 */
//JNIEXPORT jstring JNICALL Java_PJLink_MLGetSymbol
//  (JNIEnv *, jclass, jlong);
static PyObject *PJLink_MLGetSymbol
    ( PyObject *, PyObject *);

/*
 * Class:     PJLink_NativeLink
 * Method:    MLPutSymbol
 * Signature: (JLjava/lang/String;)V
 */
//JNIEXPORT void JNICALL Java_PJLink_MLPutSymbol
//  (JNIEnv *, jclass, jlong, jstring);
static PyObject *PJLink_MLPutSymbol
    ( PyObject *, PyObject *);


/*
 * Class:     PJLink_NativeLink
 * Method:    MLGetInteger
 * Signature: (J)I
 */
//JNIEXPORT jint JNICALL Java_PJLink_MLGetInteger
//  (JNIEnv *, jclass, jlong);
static PyObject *PJLink_MLGetInteger
    ( PyObject *, PyObject *);

/*
 * Class:     PJLink_NativeLink
 * Method:    MLPutInteger
 * Signature: (JI)V
 */
//JNIEXPORT void JNICALL Java_PJLink_MLPutInteger
//  (JNIEnv *, jclass, jlong, jint);
static PyObject *PJLink_MLPutInteger
    ( PyObject *, PyObject *);


/*
 * Class:     PJLink_NativeLink
 * Method:    MLGetDouble
 * Signature: (J)D
 */
//JNIEXPORT jdouble JNICALL Java_PJLink_MLGetDouble
//  (JNIEnv *, jclass, jlong);
static PyObject *PJLink_MLGetDouble
    ( PyObject *, PyObject *);

/*
 * Class:     PJLink_NativeLink
 * Method:    MLPutDouble
 * Signature: (JD)V
 */
//JNIEXPORT void JNICALL Java_PJLink_MLPutDouble
//  (JNIEnv *, jclass, jlong, jdouble);
static PyObject *PJLink_MLPutDouble
    ( PyObject *, PyObject *);


/*
 * Class:     PJLink_NativeLink
 * Method:    MLPutArray
 * Signature: (JILjava/lang/Object;Ljava/lang/String;)V
 */
//JNIEXPORT void JNICALL Java_PJLink_MLPutArray
//  (JNIEnv *, jclass, jlong, jint, jobject, jstring);
static PyObject *PJLink_MLPutArray
    ( PyObject *, PyObject *);

/*
 * Class:     PJLink_NativeLink
 * Method:    MLPutArrayFlat
 * Signature: (JILjava/lang/Object;[Ljava/lang/String;[I)V
 */
//JNIEXPORT void JNICALL Java_PJLink_MLPutArrayFlat
//  (JNIEnv *, jclass, jlong, jint, jobject, jobjectArray, jintArray);
static PyObject *PJLink_MLPutArrayFlat
    ( PyObject *, PyObject *);

/*
 * Class:     PJLink_NativeLink
 * Method:    MLGetArray
 * Signature: (JII[Ljava/lang/String;)Ljava/lang/Object;
 */
//JNIEXPORT jobject JNICALL Java_PJLink_MLGetArray
//  (JNIEnv *, jclass, jlong, jint, jint, jobjectArray);
static PyObject *PJLink_MLGetArray
    ( PyObject *, PyObject *);

/*
 * Class:     PJLink_NativeLink
 * Method:    MLCheckFunction
 * Signature: (JLjava/lang/String;)I
 */
//JNIEXPORT jint JNICALL Java_PJLink_MLCheckFunction
//  (JNIEnv *, jclass, jlong, jstring);
static PyObject *PJLink_MLCheckFunction
    ( PyObject *, PyObject *);


/*
 * Class:     PJLink_NativeLink
 * Method:    MLCheckFunctionWithArgCount
 * Signature: (JLjava/lang/String;I)I
 */
//JNIEXPORT jint JNICALL Java_PJLink_MLCheckFunctionWithArgCount
//  (JNIEnv *, jclass, jlong, jstring, jint);
static PyObject *PJLink_MLCheckFunctionWithArgCount
    ( PyObject *, PyObject *);


/*
 * Class:     PJLink_NativeLink
 * Method:    MLTransferExpression
 * Signature: (JJ)V
 */
//JNIEXPORT void JNICALL Java_PJLink_MLTransferExpression
//  (JNIEnv *, jclass, jlong, jlong);
static PyObject *PJLink_MLTransferExpression
    ( PyObject *, PyObject *);


/*
 * Class:     PJLink_NativeLink
 * Method:    MLTransferToEndOfLoopbackLink
 * Signature: (JJ)V
 */
//JNIEXPORT void JNICALL Java_PJLink_MLTransferToEndOfLoopbackLink
//  (JNIEnv *, jclass, jlong, jlong);
static PyObject *PJLink_MLTransferToEndOfLoopbackLink
    ( PyObject *, PyObject *);


/*
 * Class:     PJLink_NativeLink
 * Method:    MLGetMessage
 * Signature: (J)I
 */
//JNIEXPORT jint JNICALL Java_PJLink_MLGetMessage
//  (JNIEnv *, jclass, jlong);
static PyObject *PJLink_MLGetMessage
    ( PyObject *, PyObject *);

/*
 * Class:     PJLink_NativeLink
 * Method:    MLPutMessage
 * Signature: (JI)V
 */
//JNIEXPORT void JNICALL Java_PJLink_MLPutMessage
//  (JNIEnv *, jclass, jlong, jint);
static PyObject *PJLink_MLPutMessage
    ( PyObject *, PyObject *);


/*
 * Class:     PJLink_NativeLink
 * Method:    MLMessageReady
 * Signature: (J)Z
 */
//JNIEXPORT jboolean JNICALL Java_PJLink_MLMessageReady
//  (JNIEnv *, jclass, jlong);
static PyObject *PJLink_MLMessageReady
    ( PyObject *, PyObject *);

/*
 * Class:     PJLink_NativeLink
 * Method:    MLCreateMark
 * Signature: (J)J
 */
//JNIEXPORT jlong JNICALL Java_PJLink_MLCreateMark
//  (JNIEnv *, jclass, jlong);
static PyObject *PJLink_MLCreateMark
    ( PyObject *, PyObject *);

/*
 * Class:     PJLink_NativeLink
 * Method:    MLSeekMark
 * Signature: (JJ)V
 */
//JNIEXPORT void JNICALL Java_PJLink_MLSeekMark
//  (JNIEnv *, jclass, jlong, jlong);
static PyObject *PJLink_MLSeekMark
    ( PyObject *, PyObject *);


/*
 * Class:     PJLink_NativeLink
 * Method:    MLDestroyMark
 * Signature: (JJ)V
 */
//JNIEXPORT void JNICALL Java_PJLink_MLDestroyMark
//  (JNIEnv *, jclass, jlong, jlong);
static PyObject *PJLink_MLDestroyMark
    ( PyObject *, PyObject *);


/*
 * Class:     PJLink_NativeLink
 * Method:    MLSetYieldFunction
 * Signature: (JZ)V
 */
//JNIEXPORT void JNICALL Java_PJLink_MLSetYieldFunction
//  (JNIEnv *, jclass, jlong, jboolean);
static PyObject *PJLink_MLSetYieldFunction
    ( PyObject *, PyObject *);


/*
 * Class:     PJLink_NativeLink
 * Method:    MLSetMessageHandler
 * Signature: (J)V
 */
//JNIEXPORT void JNICALL Java_PJLink_MLSetMessageHandler
//  (JNIEnv *, jclass, jlong);
static PyObject *PJLink_MLSetMessageHandler
    ( PyObject *, PyObject *);

/*
 * Class:     PJLink_NativeLink
 * Method:    nativeSizesMatch
 * Signature: (I)Z
 */
//JNIEXPORT jboolean JNICALL Java_PJLink_nativeSizesMatch
//  (JNIEnv *, jclass, jint);
//static PyObject *PJLink_nativeSizesMatch
//    ( PyObject *, PyObject *);

/*
 * Class:     PJLink_NativeLink
 * Method:    hideJavaWindow
 * Signature: ()V
 */
//JNIEXPORT void JNICALL Java_PJLink_hideJavaWindow
//  (JNIEnv *, jclass);

/*
 * Class:     PJLink_NativeLink
 * Method:    macJavaLayerToFront
 * Signature: ()V
 */
//JNIEXPORT void JNICALL Java_PJLink_macJavaLayerToFront
//  (JNIEnv *, jclass);

/*
 * Class:     PJLink_NativeLink
 * Method:    winJavaLayerToFront
 * Signature: (Z)V
 */
//JNIEXPORT void JNICALL Java_PJLink_winJavaLayerToFront
//  (JNIEnv *, jclass, jboolean);

/*
 * Class:     PJLink_NativeLink
 * Method:    mathematicaToFront
 * Signature: ()V
 */
//JNIEXPORT void JNICALL Java_PJLink_mathematicaToFront
//  (JNIEnv *, jclass);
//static PyObject *PJLink_mathematicaToFront
//    ();

/*
 * Class:     PJLink_NativeLink
 * Method:    getNativeWindowHandle
 * Signature: (Ljava/awt/Window;Ljava/lang/String;)J
 */
//JNIEXPORT jlong JNICALL Java_PJLink_getNativeWindowHandle
//  (JNIEnv *, jclass, jobject, jstring);
//static PyObject *PJLink_getNativeWindowHandle
//    ( PyObject *);


/*
 * Class:     PJLink_NativeLink
 * Method:    killProcess
 * Signature: (J)I
 */
//JNIEXPORT jint JNICALL Java_PJLink_killProcess
//  (JNIEnv *, jclass, jlong);
//static PyObject *PJLink_killProcess
//    ( PyObject *);

/*
 * Class:     PJLink_NativeLink
 * Method:    appToFront
 * Signature: (J)V
 */
//JNIEXPORT void JNICALL Java_PJLink_appToFront
//  (JNIEnv *, jclass, jlong);
//static PyObject *PJLink_appToFront
//    ( PyObject *);

#ifdef __cplusplus
}
#endif
#endif
